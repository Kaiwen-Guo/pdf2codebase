# VerifAIX Software Generation and Testing Automation

This repository implements an auditable pipeline for the take-home assignment. It reads an English software-module description, extracts a normalized project spec, generates a structured test plan, generates a Python codebase manifest and pytest tests, executes the tests, and stores traceable artifacts/results in SQLite.

The implementation is intentionally shaped as a small CLI package. The primary generation path is configurable OpenAI-backed LLM generation, while `config.local.toml` provides a deterministic no-key path for the provided task-scheduler sample so the demo is reproducible.

## Quick Start

### Environment Setup

Use Python 3.11 or newer. The project itself only uses the standard library at runtime; `pytest` is needed for tests and generated-test execution.

Recommended setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If you do not install the package, prefix commands with `PYTHONPATH=src` as shown below.

PDF extraction uses the `pdftotext` command when available. On macOS:

```bash
brew install poppler
```

For live LLM generation, set an OpenAI API key:

```bash
export OPENAI_API_KEY=...
```

No API key is required for the deterministic local demo.

```bash
PYTHONPATH=src python -m verifaix_pipeline init-db --config config.local.toml
PYTHONPATH=src python -m verifaix_pipeline run --pdf examples/scheduler.pdf --config config.local.toml
PYTHONPATH=src python -m verifaix_pipeline delta --old-pdf examples/scheduler.pdf --new-pdf examples/scheduler_reverse.txt --config config.local.toml
PYTHONPATH=src python -m verifaix_pipeline validate-run --artifact-dir artifacts/<run_id>
python -m pytest -q
```

For live LLM generation with deterministic fallback enabled, set `OPENAI_API_KEY` and use `config.example.toml`:

```bash
export OPENAI_API_KEY=...
PYTHONPATH=src python -m verifaix_pipeline run --pdf examples/scheduler.pdf --config config.example.toml
```

For a strict live-LLM smoke test that fails if the LLM call fails, use:

```bash
export OPENAI_API_KEY=...
PYTHONPATH=src python -m verifaix_pipeline run --pdf examples/scheduler.pdf --config config.live.toml
```

## Architecture

The pipeline has eight stages:

1. Extract text from a PDF using `pdftotext` when available, with an optional `pypdf` fallback.
2. Normalize and hash the extracted description.
3. Generate `project_spec.json` with public APIs, `REQ_*` requirements, constraints, and module name.
4. Generate `test_plan.json` with `TP_*` items linked to requirement IDs and source sections.
5. Generate `codebase_manifest.json` with source files and generated pytest tests.
6. Write generated artifacts under `artifacts/<run_id>/`.
7. Execute generated tests in that isolated artifact directory with `PYTHONPATH` pointed at generated source.
8. If pytest fails in live mode, perform one LLM repair attempt using the failure output and rerun validation/tests.
9. Persist descriptions, project specs, requirements, plans, generated files, prompts, validation reports, deltas, test results, and trace links in SQLite.

The key design goal is auditability: the database and artifact directory preserve what description was used, what prompts were sent, what code/tests were generated, and which test-plan item each result maps back to.

Prompting is layered. Shared artifact contracts live under `prompts/blueprints/`; task-specific LLM behavior lives under `prompts/skills/`. See [docs/prompt_layering.md](docs/prompt_layering.md).

## CLI

```bash
verifaix init-db --config config.local.toml
verifaix run --pdf path/to/problem.pdf --config config.local.toml
verifaix delta --old-pdf old.pdf --new-pdf new.pdf --config config.local.toml
verifaix validate-run --artifact-dir artifacts/<run_id>
verifaix show-runs --db verifaix.local.db
```

If the package is not installed, use `PYTHONPATH=src python -m verifaix_pipeline ...`.

## Generated Codebase Location

Each run writes an interactable generated codebase under:

```text
artifacts/<run_id>/
  README.md
  pyproject.toml
  main.py
  project_spec.json
  test_plan.json
  codebase_manifest.json
  generated/
    <generated source modules>
  tests/
    test_generated.py
  pytest_stdout.txt
  pytest_stderr.txt
```

For example, the checked assignment-PDF output can be run directly from the repository:

```bash
cd submission_output/live_scheduler
PYTHONPATH=generated python main.py
PYTHONPATH=generated python -m pytest -q tests/test_generated.py
PYTHONPATH=generated python - <<'PY'
from task_scheduler import schedule_tasks
print(schedule_tasks(["b", "a", "c"], []))
PY
```

The non-scheduler live demo is:

```bash
cd submission_output/live_slugify
PYTHONPATH=generated python main.py
PYTHONPATH=generated python -m pytest -q tests/test_generated.py
PYTHONPATH=generated python - <<'PY'
from slugify_utility import slugify
print(slugify(" Hello, World! "))
PY
```

Delta does not convert a PDF into another PDF. It compares two versions of the description, regenerates/compares their structured requirements and test-plan context, and reports which tests/code should change. In this assignment, delta is an audit artifact for requirement drift.

## Configuration

`config.example.toml` demonstrates the live OpenAI path:

- `llm_provider = "openai"`
- `model_name`
- `api_key_env`
- `temperature`
- `use_llm_for_testplan`
- `use_llm_for_code`
- `use_llm_for_tests`

`config.local.toml` disables LLM calls and uses the deterministic scheduler fallback. That fallback is intentionally scoped to the sample problem; hidden PDFs should use the configured LLM path. `config.live.toml` disables fallback so live LLM failures are visible.

## Database Content

SQLite tables are initialized by the app:

- `description_versions`
- `project_specs`
- `requirements`
- `test_plans`
- `test_plan_items`
- `deltas`
- `generated_code`
- `generated_tests`
- `generated_files`
- `execution_results`
- `trace_links`
- `validation_reports`

Prompts are composed from `prompts/blueprints/` and `prompts/skills/`, then persisted per run in `artifacts/<run_id>/prompts.json`.

## Current Demo Output

The full live run against `Problem_Description_Software_Coding.pdf` generated:

- `project_spec.json`
- `codebase_manifest.json`
- `task_scheduler.py`
- `test_generated.py`
- `test_plan.json`
- `pytest_stdout.txt`
- SQLite rows for descriptions, test-plan items, generated code/tests, execution results, and trace links

The checked-in deterministic sample output is under `submission_output/sample_scheduler/`. The checked-in live-LLM scheduler output from the assignment PDF is under `submission_output/live_scheduler/`. A second non-scheduler live output is under `submission_output/live_slugify/`.

The reverse-parameter delta demo reports added/modified test-plan obligations caused by adding `reverse`.

## Tests

The repository tests cover PDF extraction, deterministic test-plan generation, delta detection, full local pipeline execution, and database result persistence.

```bash
python -m pytest -q
```

## Prompts and LLMs Used

No live LLM calls are required for the local demo. The live path is implemented through the configurable OpenAI adapter. Prompt building blocks used by the pipeline are in:

- `prompts/blueprints/`
- `prompts/skills/`
