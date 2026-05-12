# Prompt Layering

The pipeline separates prompt concerns into two layers: blueprints and skills.

## Blueprints

Blueprints are stable contracts shared across tasks. They define artifact shape and quality expectations, not the task itself.

- `blueprints/system_context.txt`: global pipeline role and source-of-truth rules.
- `blueprints/response_discipline.txt`: output-only, no markdown fences, concise responses.
- `blueprints/test_plan_schema.txt`: JSON shape and rules for test plans.
- `blueprints/code_contract.txt`: importable Python module requirements.
- `blueprints/project_spec_schema.txt`: normalized public API and `REQ_*` requirement schema.
- `blueprints/codebase_manifest_schema.txt`: generated codebase file manifest schema.
- `blueprints/pytest_contract.txt`: pytest naming and traceability contract.
- `blueprints/delta_schema.txt`: delta JSON shape and semantic comparison rules.
- `blueprints/traceability.txt`: source-section, TP ID, and test-result linkage rules.

## Skills

Skills are task-specific instructions. They say what transformation the LLM should perform.

- `skills/test_plan_generator.txt`: PDF requirement text to structured test plan.
- `skills/spec_extractor.txt`: PDF requirement text to normalized project spec.
- `skills/codebase_generator.txt`: project spec plus test plan to generated codebase manifest.
- `skills/pytest_generator.txt`: test plan to executable pytest tests.
- `skills/delta_analyzer.txt`: old/new descriptions and plans to semantic deltas.
- `skills/repair_generator.txt`: failed generated codebase plus pytest output to replacement manifest.

## Composition

Each pipeline stage composes a prompt from several blueprints plus one skill:

```text
spec prompt      = system + response discipline + project-spec schema + traceability + spec skill
test-plan prompt = system + response discipline + test-plan schema + traceability + test-plan skill
codebase prompt  = system + response discipline + code contract + manifest schema + traceability + codebase skill
tests prompt     = system + response discipline + pytest contract + traceability + pytest skill
delta prompt     = system + response discipline + delta schema + traceability + delta skill
repair prompt    = system + response discipline + code contract + manifest schema + pytest contract + traceability + repair skill
```

This keeps prompts easier to maintain. If traceability expectations change, update one blueprint instead of four separate task prompts.
