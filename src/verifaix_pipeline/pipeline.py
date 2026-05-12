from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import time
from uuid import uuid4

from .config import AppConfig
from .db import Database
from .generators import (
    generate_codebase,
    generate_deltas,
    generate_project_spec,
    generate_test_plan,
    generate_tests,
    repair_codebase,
)
from .llm import LLMClient
from .models import CodebaseManifest, Delta, GeneratedFile, ProjectSpec, TestPlan
from .pdf import extract_description
from .validation import (
    validate_artifact_paths,
    validate_codebase_manifest,
    validate_generated_test_coverage,
    validate_project_spec,
    validate_python_source,
    validate_requirement_coverage,
    validate_test_plan_against_description,
)


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    description_version_id: int
    plan_id: int
    module_name: str
    artifact_dir: Path
    pytest_returncode: int
    passed: int
    failed: int


def initialize_database(config: AppConfig) -> dict[str, int]:
    database = Database(config.storage.database_path)
    try:
        database.init_schema()
        return database.counts()
    finally:
        database.close()


def run_pipeline(pdf_path: str | Path, config: AppConfig) -> RunSummary:
    database = Database(config.storage.database_path)
    database.init_schema()
    try:
        llm_client = LLMClient(config.llm)
        description = extract_description(
            pdf_path,
            extraction_config=config.extraction,
            llm_config=config.llm,
        )
        description_id = database.insert_description(
            description.pdf_path,
            description.text_hash,
            description.text,
        )
        project_spec, spec_prompt = generate_project_spec(
            description.text,
            llm_client,
            config.llm.use_llm_for_testplan,
            config.runtime.fallback_to_deterministic,
        )
        validate_project_spec(project_spec)
        database.insert_project_spec(description_id, project_spec)
        test_plan, testplan_prompt = generate_test_plan(
            description.text,
            project_spec,
            llm_client,
            config.llm.use_llm_for_testplan,
            config.runtime.fallback_to_deterministic,
        )
        validate_test_plan_against_description(description.text, test_plan)
        validate_requirement_coverage(project_spec, test_plan)
        plan_id = database.insert_test_plan(description_id, test_plan)
        module_name = project_spec.module_name
        source_manifest, code_prompt = generate_codebase(
            project_spec,
            test_plan,
            llm_client,
            config.llm.use_llm_for_code,
            config.runtime.fallback_to_deterministic,
        )
        tests_text, tests_prompt = generate_tests(
            description.text,
            test_plan,
            module_name,
            llm_client,
            config.llm.use_llm_for_tests,
            config.runtime.fallback_to_deterministic,
        )
        validate_python_source(tests_text, "Generated tests")
        validate_generated_test_coverage(test_plan, tests_text)

        run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        artifact_dir = config.storage.artifacts_dir / run_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        source_files = [
            _materialize_source_file(file) for file in source_manifest.files
        ]
        tests_file = GeneratedFile(
            path="tests/test_generated.py",
            kind="test",
            purpose="generated pytest suite",
            content=tests_text,
        )
        scaffold_files = scaffold_project_files(project_spec, test_plan)
        manifest = CodebaseManifest(
            entry_module=module_name,
            files=[*source_files, tests_file, *scaffold_files],
        )
        validate_codebase_manifest(manifest)
        module_file = next(file for file in manifest.files if file.kind == "source")
        code_text = module_file.content
        module_path = artifact_dir / module_file.path
        tests_path = artifact_dir / tests_file.path
        plan_path = artifact_dir / "test_plan.json"
        spec_path = artifact_dir / "project_spec.json"
        manifest_path = artifact_dir / "codebase_manifest.json"
        prompts_path = artifact_dir / "prompts.json"
        for file in manifest.files:
            output_path = artifact_dir / file.path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(file.content, encoding="utf-8")
        spec_path.write_text(
            json.dumps(project_spec.to_dict(), indent=2), encoding="utf-8"
        )
        plan_path.write_text(json.dumps(test_plan.to_dict(), indent=2), encoding="utf-8")
        manifest_path.write_text(
            json.dumps(manifest.to_dict(), indent=2), encoding="utf-8"
        )
        prompts_path.write_text(
            json.dumps(
                {
                    "project_spec": spec_prompt,
                    "testplan": testplan_prompt,
                    "codebase": code_prompt,
                    "tests": tests_prompt,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        validate_artifact_paths(
            [module_path, tests_path, spec_path, plan_path, manifest_path, prompts_path]
        )
        database.insert_validation_report(run_id, "pre_pytest", "passed", "Artifacts validated")

        database.insert_generated_code(
            description_id, module_name, str(module_path), code_text, code_prompt
        )
        database.insert_generated_tests(plan_id, str(tests_path), tests_text, tests_prompt)
        database.insert_generated_files(description_id, run_id, manifest)

        pytest_result = execute_generated_tests(artifact_dir, tests_file.path)
        if pytest_result.returncode != 0 and llm_client.enabled:
            repaired_manifest, repair_prompt = repair_codebase(
                project_spec,
                test_plan,
                manifest,
                pytest_result.stdout + pytest_result.stderr,
                llm_client,
            )
            repaired_files = [
                _materialize_source_file(file) for file in repaired_manifest.files
            ]
            if not any(file.kind == "test" for file in repaired_files):
                repaired_files.append(tests_file)
            repaired_paths = {file.path for file in repaired_files}
            repaired_files.extend(
                file
                for file in scaffold_project_files(project_spec, test_plan)
                if file.path not in repaired_paths
            )
            manifest = CodebaseManifest(
                entry_module=repaired_manifest.entry_module,
                files=repaired_files,
            )
            validate_codebase_manifest(manifest)
            repaired_test_file = next(
                (file for file in manifest.files if file.kind == "test"), tests_file
            )
            validate_generated_test_coverage(test_plan, repaired_test_file.content)
            for file in manifest.files:
                output_path = artifact_dir / file.path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(file.content, encoding="utf-8")
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2), encoding="utf-8"
            )
            tests_file = repaired_test_file
            tests_path = artifact_dir / tests_file.path
            prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
            prompts["repair"] = repair_prompt
            prompts_path.write_text(json.dumps(prompts, indent=2), encoding="utf-8")
            database.insert_validation_report(
                run_id, "repair", "attempted", "Performed one LLM repair attempt"
            )
            pytest_result = execute_generated_tests(artifact_dir, tests_file.path)
        test_names = collect_test_names(artifact_dir, tests_file.path)
        outcomes = map_pytest_outcomes(test_names, pytest_result)

        item_by_tp = {item.tp_id: item for item in test_plan.items}
        passed = 0
        failed = 0
        for test_name, outcome in outcomes.items():
            tp_id = tp_id_from_test_name(test_name)
            if outcome == "passed":
                passed += 1
            else:
                failed += 1
            result_id = database.insert_execution_result(
                run_id,
                test_name,
                tp_id,
                outcome,
                pytest_result.stderr + pytest_result.stdout if outcome != "passed" else "",
                0.0,
            )
            item = item_by_tp.get(tp_id)
            source_sections = item.source_sections if item else [""]
            for section in source_sections or [""]:
                database.insert_trace_link(
                    description_id, section, tp_id, test_name, result_id
                )

        (artifact_dir / "pytest_stdout.txt").write_text(
            pytest_result.stdout, encoding="utf-8"
        )
        (artifact_dir / "pytest_stderr.txt").write_text(
            pytest_result.stderr, encoding="utf-8"
        )
        database.insert_validation_report(
            run_id,
            "pytest",
            "passed" if pytest_result.returncode == 0 else "failed",
            pytest_result.stdout + pytest_result.stderr,
        )

        return RunSummary(
            run_id=run_id,
            description_version_id=description_id,
            plan_id=plan_id,
            module_name=module_name,
            artifact_dir=artifact_dir,
            pytest_returncode=pytest_result.returncode,
            passed=passed,
            failed=failed,
        )
    finally:
        database.close()


def run_delta(
    old_pdf_path: str | Path,
    new_pdf_path: str | Path,
    config: AppConfig,
) -> list[Delta]:
    database = Database(config.storage.database_path)
    database.init_schema()
    try:
        llm_client = LLMClient(config.llm)
        old_description = extract_description(
            old_pdf_path,
            extraction_config=config.extraction,
            llm_config=config.llm,
        )
        new_description = extract_description(
            new_pdf_path,
            extraction_config=config.extraction,
            llm_config=config.llm,
        )
        old_id = database.insert_description(
            old_description.pdf_path,
            old_description.text_hash,
            old_description.text,
        )
        new_id = database.insert_description(
            new_description.pdf_path,
            new_description.text_hash,
            new_description.text,
        )
        old_plan, _ = generate_test_plan(
            old_description.text,
            generate_project_spec(
                old_description.text,
                llm_client,
                config.llm.use_llm_for_testplan,
                config.runtime.fallback_to_deterministic,
            )[0],
            llm_client,
            config.llm.use_llm_for_testplan,
            config.runtime.fallback_to_deterministic,
        )
        new_plan, _ = generate_test_plan(
            new_description.text,
            generate_project_spec(
                new_description.text,
                llm_client,
                config.llm.use_llm_for_testplan,
                config.runtime.fallback_to_deterministic,
            )[0],
            llm_client,
            config.llm.use_llm_for_testplan,
            config.runtime.fallback_to_deterministic,
        )
        database.insert_test_plan(old_id, old_plan)
        database.insert_test_plan(new_id, new_plan)
        deltas, _ = generate_deltas(
            old_plan,
            new_plan,
            llm_client,
            config.llm.use_llm_for_testplan,
            config.runtime.fallback_to_deterministic,
            old_description.text,
            new_description.text,
        )
        database.insert_deltas(old_id, new_id, deltas)
        return deltas
    finally:
        database.close()


def execute_generated_tests(
    artifact_dir: Path, tests_path: str = "test_generated.py"
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str((artifact_dir / "generated").resolve())}
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", tests_path, "--tb=short"],
        cwd=artifact_dir,
        text=True,
        capture_output=True,
        env=env,
    )


def collect_test_names(artifact_dir: Path, tests_path: str = "test_generated.py") -> list[str]:
    env = {**os.environ, "PYTHONPATH": str((artifact_dir / "generated").resolve())}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", tests_path],
        cwd=artifact_dir,
        text=True,
        capture_output=True,
        env=env,
    )
    names = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" in line and "test_generated.py::" in line:
            names.append(line.rsplit("::", 1)[1])
    return names


def map_pytest_outcomes(
    test_names: list[str],
    pytest_result: subprocess.CompletedProcess[str],
) -> dict[str, str]:
    outcomes = {name: "passed" for name in test_names}
    if pytest_result.returncode == 0:
        return outcomes
    failed = set()
    for match in re.finditer(
        r"FAILED .*test_generated\.py::([A-Za-z0-9_]+)", pytest_result.stdout
    ):
        failed.add(match.group(1))
    if failed:
        for name in failed:
            outcomes[name] = "failed"
        return outcomes
    return {name: "failed" for name in test_names}


def tp_id_from_test_name(test_name: str) -> str:
    match = re.search(r"test_tp_(\d+)", test_name, flags=re.IGNORECASE)
    if not match:
        return ""
    return f"TP_{int(match.group(1))}"


def load_plan_from_json(path: str | Path) -> TestPlan:
    return TestPlan.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def validate_artifact_dir(artifact_dir: str | Path) -> dict[str, str]:
    root = Path(artifact_dir)
    spec = json.loads((root / "project_spec.json").read_text(encoding="utf-8"))
    plan = json.loads((root / "test_plan.json").read_text(encoding="utf-8"))
    manifest_json = json.loads(
        (root / "codebase_manifest.json").read_text(encoding="utf-8")
    )
    from .models import ProjectSpec

    project_spec = ProjectSpec.from_dict(spec)
    test_plan = TestPlan.from_dict(plan)
    manifest = CodebaseManifest.from_dict(manifest_json)
    validate_project_spec(project_spec)
    validate_test_plan_against_description("", test_plan)
    validate_requirement_coverage(project_spec, test_plan)
    validate_codebase_manifest(manifest)
    validate_artifact_paths([root / file.path for file in manifest.files])
    test_file = next((file for file in manifest.files if file.kind == "test"), None)
    if test_file:
        validate_generated_test_coverage(test_plan, test_file.content)
    return {
        "project_spec": "passed",
        "test_plan": "passed",
        "codebase_manifest": "passed",
        "artifacts": "passed",
    }


def _materialize_source_file(file: GeneratedFile) -> GeneratedFile:
    if file.kind == "test" or file.path.startswith("generated/"):
        return file
    return GeneratedFile(
        path=f"generated/{file.path}",
        kind=file.kind,
        purpose=file.purpose,
        content=file.content,
    )


def scaffold_project_files(project_spec: ProjectSpec, test_plan: TestPlan) -> list[GeneratedFile]:
    project_slug = re.sub(r"[^a-z0-9_-]+", "-", project_spec.project_name.lower()).strip("-")
    project_slug = project_slug or project_spec.module_name.replace("_", "-")
    public_api_lines = "\n".join(
        f"- `{api.signature}`: {api.description or api.name}"
        for api in project_spec.public_api
    )
    requirement_lines = "\n".join(
        f"- `{requirement.req_id}` [{requirement.category}]: {requirement.description}"
        for requirement in project_spec.requirements
    )
    test_lines = "\n".join(
        f"- `{item.tp_id}` -> {', '.join(item.requirement_ids or []) or 'unmapped'}: {item.description}"
        for item in test_plan.items
    )
    readme = f"""# {project_spec.project_name}

Generated Python project from an English software specification.

## Public API

{public_api_lines}

## Requirements

{requirement_lines}

## Test Plan Trace

{test_lines}

## Run

```bash
python main.py
python -m pytest -q
```

## Generated Layout

```text
generated/          # generated source modules
tests/              # generated pytest suite
project_spec.json   # normalized requirements and public APIs
test_plan.json      # executable test-plan items
codebase_manifest.json
```
"""
    pyproject = f"""[project]
name = "{project_slug}"
version = "0.1.0"
description = "Generated project from a VerifAIX requirements pipeline."
requires-python = ">=3.11"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["generated"]
"""
    apis_repr = repr(
        [
            {
                "name": api.name,
                "kind": api.kind,
                "signature": api.signature,
                "description": api.description,
            }
            for api in project_spec.public_api
        ]
    )
    main_py = f'''from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys


MODULE_NAME = "{project_spec.module_name}"
PUBLIC_APIS = {apis_repr}


GENERATED_DIR = Path(__file__).resolve().parent / "generated"
if str(GENERATED_DIR) not in sys.path:
    sys.path.insert(0, str(GENERATED_DIR))


def main() -> None:
    module = import_module(MODULE_NAME)
    print(f"Generated project: {project_spec.project_name}")
    print(f"Entry module: {{MODULE_NAME}}")
    print("Public API:")
    for api in PUBLIC_APIS:
        name = api["name"]
        signature = api["signature"]
        description = api.get("description") or name
        available = hasattr(module, name)
        status = "available" if available else "missing"
        print(f"- {{signature}} [{{status}}]: {{description}}")


if __name__ == "__main__":
    main()
'''
    return [
        GeneratedFile("README.md", "support", "generated project documentation", readme),
        GeneratedFile("pyproject.toml", "support", "project metadata and pytest config", pyproject),
        GeneratedFile("main.py", "support", "runnable project entrypoint", main_py),
    ]
