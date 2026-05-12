from __future__ import annotations

from pathlib import Path
import sqlite3

from verifaix_pipeline.config import load_config
from verifaix_pipeline.generators import (
    clean_deltas,
    compare_test_plans,
    deterministic_test_plan,
    filter_deltas_against_descriptions,
)
from verifaix_pipeline.llm import compose_prompt
from verifaix_pipeline.models import TestPlan as PlanModel
from verifaix_pipeline.models import TestPlanItem as PlanItemModel
from verifaix_pipeline.models import Delta
from verifaix_pipeline.models import CodebaseManifest, GeneratedFile, ProjectSpec, PublicAPI, Requirement
from verifaix_pipeline.pdf import extract_description
from verifaix_pipeline.pipeline import run_delta, run_pipeline
from verifaix_pipeline.validation import (
    validate_codebase_manifest,
    validate_generated_test_coverage,
    validate_project_spec,
    validate_python_source,
    validate_test_plan_against_description,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PDF = ROOT / "Problem_Description_Software_Coding.pdf"
REVERSE_TEXT = ROOT / "examples" / "scheduler_reverse.txt"


def test_extract_description_from_pdf():
    description = extract_description(SAMPLE_PDF)
    assert "schedule_tasks" in description.text
    assert len(description.text_hash) == 64


def test_deterministic_plan_has_traceable_items():
    description = extract_description(SAMPLE_PDF)
    plan = deterministic_test_plan(description.text)
    assert len(plan.items) == 20
    assert plan.items[0].tp_id == "TP_1"
    assert plan.items[0].source_sections == ["1.1"]


def test_delta_detects_added_and_modified_items():
    old_plan = PlanModel(
        [
            PlanItemModel("TP_1", "Old behavior", ["1.1"], "old", "behavior"),
            PlanItemModel("TP_2", "Removed behavior", ["1.2"], "removed", "behavior"),
        ]
    )
    new_plan = PlanModel(
        [
            PlanItemModel("TP_1", "New behavior", ["1.1"], "new", "behavior"),
            PlanItemModel("TP_3", "Added behavior", ["1.3"], "added", "behavior"),
        ]
    )
    deltas = compare_test_plans(old_plan, new_plan)
    assert [(delta.change_type, delta.tp_id) for delta in deltas] == [
        ("Modified", "TP_1"),
        ("Added", "TP_3"),
        ("Removed", "TP_2"),
    ]


def test_prompt_composition_layers_blueprints_and_skills():
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/test_plan_schema.txt",
            "skills/test_plan_generator.txt",
        ],
        description_text="1.1 API\nsample_function()",
    )
    assert "auditable requirements-to-code pipeline" in prompt
    assert '"tp_id": "TP_1"' in prompt
    assert "sample_function()" in prompt


def test_generated_artifact_validators_catch_bad_outputs():
    plan = PlanModel(
        [
            PlanItemModel("TP_1", "First behavior", ["1.1"], "first", "behavior"),
            PlanItemModel("TP_2", "Second behavior", ["1.1"], "second", "behavior"),
        ]
    )
    validate_python_source("def test_tp_1_ok():\n    assert True\n", "tests")
    try:
        validate_generated_test_coverage(plan, "def test_tp_1_ok():\n    assert True\n")
    except ValueError as exc:
        assert "TP_2" in str(exc)
    else:
        raise AssertionError("missing TP coverage was not detected")


def test_plan_validator_requires_categories_from_description():
    plan = PlanModel(
        [PlanItemModel("TP_1", "Behavior", ["1.2"], "works", "behavior")]
    )
    description = "1.1 API\nx()\n\n1.5 Assumptions\nTask names are case-sensitive."
    try:
        validate_test_plan_against_description(description, plan)
    except ValueError as exc:
        assert "api" in str(exc)
        assert "assumption" in str(exc)
    else:
        raise AssertionError("missing category coverage was not detected")


def test_delta_cleaner_removes_noise_and_duplicates():
    deltas = clean_deltas(
        [
            Delta("D_1", "Modified", "TP_1", "Added reverse parameter"),
            Delta("D_2", "Modified", "TP_2", "Renamed old test item"),
            Delta("D_3", "Modified", "TP_1", "Duplicate affected item"),
            Delta("D_4", "Other", "TP_4", "Unsupported change type"),
            Delta("D_5", "Modified", "TP_5", "Clarified old wording"),
        ]
    )
    assert deltas == [Delta("D_1", "Modified", "TP_1", "Added reverse parameter")]


def test_delta_filter_removes_repeated_complexity_requirement():
    deltas = filter_deltas_against_descriptions(
        [
            Delta("D_1", "Added", "TP_1", "Added reverse behavior"),
            Delta("D_2", "Added", "TP_2", "Explicit complexity requirement added"),
        ],
        "Expected complexity: O(N)",
        "Expected complexity: O(N). Reverse parameter added.",
    )
    assert deltas == [Delta("D_1", "Added", "TP_1", "Added reverse behavior")]


def test_project_spec_and_manifest_validators_reject_unsafe_outputs():
    spec = ProjectSpec(
        project_name="Example",
        module_name="bad/module",
        public_api=[
            PublicAPI("thing", "function", "thing()", "does thing", ["1.1"])
        ],
        requirements=[
            Requirement("REQ_1", "thing works", "behavior", ["1.2"])
        ],
        constraints={"language": "python"},
    )
    try:
        validate_project_spec(spec)
    except ValueError as exc:
        assert "Unsafe module name" in str(exc)
    else:
        raise AssertionError("unsafe module name was not detected")

    manifest = CodebaseManifest(
        entry_module="example",
        files=[
            GeneratedFile("../escape.py", "source", "bad path", "x = 1\n")
        ],
    )
    try:
        validate_codebase_manifest(manifest)
    except ValueError as exc:
        assert "Unsafe generated file path" in str(exc)
    else:
        raise AssertionError("unsafe generated file path was not detected")


def test_full_pipeline_local_config(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[llm]
llm_provider = "none"
model_name = ""
api_key_env = ""
temperature = 0.0
use_llm_for_testplan = false
use_llm_for_code = false
use_llm_for_tests = false

[storage]
database_path = "{tmp_path / 'verifaix.db'}"
artifacts_dir = "{tmp_path / 'artifacts'}"

[runtime]
module_name = "generated_module"
fallback_to_deterministic = true
""",
        encoding="utf-8",
    )
    config = load_config(config_path)
    summary = run_pipeline(SAMPLE_PDF, config)
    assert summary.pytest_returncode == 0
    assert summary.passed == 20
    assert summary.failed == 0
    assert (summary.artifact_dir / "generated" / "task_scheduler.py").exists()
    assert (summary.artifact_dir / "tests" / "test_generated.py").exists()
    assert (summary.artifact_dir / "project_spec.json").exists()
    assert (summary.artifact_dir / "codebase_manifest.json").exists()
    assert (summary.artifact_dir / "test_plan.json").exists()

    with sqlite3.connect(config.storage.database_path) as connection:
        result_count = connection.execute(
            "SELECT COUNT(*) FROM execution_results"
        ).fetchone()[0]
        trace_count = connection.execute("SELECT COUNT(*) FROM trace_links").fetchone()[0]
        spec_count = connection.execute("SELECT COUNT(*) FROM project_specs").fetchone()[0]
        file_count = connection.execute("SELECT COUNT(*) FROM generated_files").fetchone()[0]
    assert result_count == 20
    assert trace_count >= 20
    assert spec_count == 1
    assert file_count >= 2


def test_delta_pipeline_local_config(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[llm]
llm_provider = "none"
model_name = ""
api_key_env = ""
temperature = 0.0
use_llm_for_testplan = false
use_llm_for_code = false
use_llm_for_tests = false

[storage]
database_path = "{tmp_path / 'verifaix.db'}"
artifacts_dir = "{tmp_path / 'artifacts'}"

[runtime]
module_name = "generated_module"
fallback_to_deterministic = true
""",
        encoding="utf-8",
    )
    config = load_config(config_path)
    deltas = run_delta(SAMPLE_PDF, REVERSE_TEXT, config)
    assert ("Modified", "TP_8") in [(delta.change_type, delta.tp_id) for delta in deltas]
    assert ("Added", "TP_24") in [(delta.change_type, delta.tp_id) for delta in deltas]
