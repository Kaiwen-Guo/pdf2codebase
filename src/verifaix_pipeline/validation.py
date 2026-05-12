from __future__ import annotations

import ast
import re
from pathlib import Path

from .models import CodebaseManifest, ProjectSpec, TestPlan


def validate_python_source(source: str, label: str) -> None:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"{label} is not valid Python: {exc}") from exc


def validate_generated_test_coverage(test_plan: TestPlan, tests_source: str) -> None:
    planned_ids = {item.tp_id for item in test_plan.items}
    covered_ids = {
        f"TP_{int(match)}"
        for match in re.findall(r"test_tp_(\d+)", tests_source, flags=re.IGNORECASE)
    }
    missing = sorted(planned_ids - covered_ids, key=_tp_sort_key)
    if missing:
        raise ValueError(
            "Generated tests do not cover test-plan items: " + ", ".join(missing)
        )


def validate_test_plan_against_description(description_text: str, test_plan: TestPlan) -> None:
    categories = {item.category.lower() for item in test_plan.items}
    lowered = description_text.lower()
    missing: list[str] = []
    if "api" in lowered and "api" not in categories:
        missing.append("api")
    if "error handling" in lowered and "error" not in categories:
        missing.append("error")
    if "boundary conditions" in lowered and "boundary" not in categories:
        missing.append("boundary")
    if "assumptions" in lowered and "assumption" not in categories:
        missing.append("assumption")
    if missing:
        raise ValueError(
            "Generated test plan is missing required category coverage: "
            + ", ".join(missing)
        )


def validate_project_spec(project_spec: ProjectSpec) -> None:
    module_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    if not module_pattern.match(project_spec.module_name):
        raise ValueError(f"Unsafe module name: {project_spec.module_name}")
    req_ids = {requirement.req_id for requirement in project_spec.requirements}
    if len(req_ids) != len(project_spec.requirements):
        raise ValueError("Project spec contains duplicate requirement IDs")
    if not project_spec.public_api:
        raise ValueError("Project spec must include public API entries")


def validate_requirement_coverage(project_spec: ProjectSpec, test_plan: TestPlan) -> None:
    planned_requirement_ids = {
        req_id
        for item in test_plan.items
        for req_id in (item.requirement_ids or [])
    }
    if planned_requirement_ids:
        spec_requirement_ids = {
            requirement.req_id for requirement in project_spec.requirements
        }
        missing_ids = sorted(spec_requirement_ids - planned_requirement_ids, key=_req_sort_key)
        if missing_ids:
            raise ValueError(
                "Test plan does not cover requirement IDs: "
                + ", ".join(missing_ids)
            )
        return

    categories = {item.category.lower() for item in test_plan.items}
    missing_categories = sorted(
        {
            requirement.category.lower()
            for requirement in project_spec.requirements
            if requirement.category.lower() not in categories
        }
    )
    if missing_categories:
        raise ValueError(
            "Test plan does not cover requirement categories: "
            + ", ".join(missing_categories)
        )


def validate_codebase_manifest(manifest: CodebaseManifest) -> None:
    seen_paths: set[str] = set()
    has_source = False
    required_support = {"README.md", "pyproject.toml", "main.py"}
    for file in manifest.files:
        path = Path(file.path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe generated file path: {file.path}")
        if file.path in seen_paths:
            raise ValueError(f"Duplicate generated file path: {file.path}")
        seen_paths.add(file.path)
        if file.kind == "source":
            has_source = True
        if file.path.endswith(".py"):
            validate_python_source(file.content, file.path)
    if not has_source:
        raise ValueError("Codebase manifest must contain at least one source file")
    missing_support = required_support - seen_paths
    if missing_support:
        raise ValueError(
            "Codebase manifest is missing project scaffolding: "
            + ", ".join(sorted(missing_support))
        )


def validate_artifact_paths(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise ValueError("Missing generated artifact(s): " + ", ".join(missing))


def _tp_sort_key(tp_id: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", tp_id)
    return (int(match.group(1)) if match else 10**9, tp_id)


def _req_sort_key(req_id: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", req_id)
    return (int(match.group(1)) if match else 10**9, req_id)
