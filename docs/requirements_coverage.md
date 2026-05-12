# Assignment Requirements Coverage

Source document: `Problem  -- Software Generation and Testing Automation.docx`.

## Input Scope

The assignment asks for a Python system that reads an English software-module description from a PDF. It does not ask for OCR, image-to-text extraction, image-to-Word extraction, or Word-document parsing as part of the pipeline. The `.docx` file is the assignment instructions; the module description input is a PDF such as `Problem_Description_Software_Coding.pdf`.

## Deliverables

| # | Requirement | Status | Implementation |
|---|---|---|---|
| 1 | Source code as an importable Python module | Met | `src/verifaix_pipeline/` is installable with `python -m pip install -e ".[dev]"`; CLI entrypoint is `verifaix`. |
| 2 | Tests for the module | Met | `tests/test_pipeline.py` covers extraction, config, prompt layering, validation, local pipeline execution, DB persistence, and delta detection. |
| 3 | Database schema or initialization logic | Met | `src/verifaix_pipeline/db.py` defines SQLite schema; `verifaix init-db` initializes it. |
| 4 | Generated test-plan output | Met | Each run writes `test_plan.json`; checked example is `submission_output/live_scheduler/test_plan.json`. |
| 5 | Generated executable test code | Met | Each run writes `tests/test_generated.py`; checked example is `submission_output/live_scheduler/tests/test_generated.py`. |
| 6 | Test execution results | Met | Pytest output is saved to `pytest_stdout.txt`/`pytest_stderr.txt`; normalized results are stored in `execution_results`. |
| 7 | Prompts used during the task | Met | Prompt building blocks are in `prompts/`; composed prompts are written to `prompts.json` per run and checked in under `submission_output/live_scheduler/prompts.json`. |
| 8 | Coding agents and/or LLMs used | Met | README documents OpenAI-backed live generation, deterministic local mode, and Codex-assisted development. |

## Functional Requirements

| Requirement | Status | Implementation |
|---|---|---|
| Generate structured English test plan from PDF description | Met | `generate_test_plan` writes `test_plan.json` with `TP_*`, source sections, categories, and expected behavior. |
| Generate Python code implementing the described module | Met | `generate_codebase` writes a source manifest and materialized Python source files. |
| Generate executable Python tests from the test plan | Met | `generate_tests` writes pytest code with traceable test IDs. |
| Save test plans, deltas, generated code, and results in a database | Met | SQLite tables include `test_plans`, `test_plan_items`, `deltas`, `generated_code`, `generated_tests`, `generated_files`, and `execution_results`. |
| Detect description changes and produce test-plan deltas | Met | `verifaix delta --old-pdf ... --new-pdf ...` produces added/removed/modified delta items. |
| Maintain traceability between description sections, test-plan items, generated tests, and results | Met | Requirements/test-plan items carry `source_sections`; generated tests include `TP_*`; `trace_links` connects source sections, test IDs, test names, and result IDs. |
| Be tested with a different problem-description PDF | Partially met by architecture | The live LLM path is general-purpose and was also tested against a non-scheduler slugify description. The deterministic fallback is intentionally sample-specific. |

## Configuration Requirements

| Setting | Status | Implementation |
|---|---|---|
| `llm_provider` | Met | Supports `openai`, `anthropic`, and `none`. |
| `model_name` | Met | Configured in TOML. |
| `api_key` or environment-variable reference | Met | Uses `api_key_env`; no key is hardcoded. |
| `temperature` | Met | Configured in TOML. |
| `database_path` | Met | Configured in TOML. |
| `use_llm_for_testplan` | Met | Configured in TOML. |
| `use_llm_for_code` | Met | Configured in TOML. |
| `use_llm_for_tests` | Met | Configured in TOML. |

## Known Non-Goals And Limitations

- The system does not perform OCR for scanned/image-only PDFs.
- The system does not convert images to Word documents.
- Generated code is executed in a local subprocess, not a hardened sandbox.
- Semantic correctness is bounded by extracted requirements and generated tests; production use would need stronger independent review or reference-test generation.
