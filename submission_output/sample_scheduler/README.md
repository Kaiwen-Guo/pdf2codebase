# Task Scheduler

Generated Python project from an English software specification.

## Public API

- `schedule_tasks(tasks: list[str], dependencies: list[tuple[str, str]]) -> list[str]`: Return a valid deterministic task execution order.

## Requirements

- `REQ_1` [api]: Module exposes callable schedule_tasks
- `REQ_2` [api]: Accepts tasks and dependencies inputs
- `REQ_3` [api]: Returns list of task names
- `REQ_4` [behavior]: Every task appears exactly once
- `REQ_5` [behavior]: Dependencies are respected in order
- `REQ_6` [boundary]: Linear chain scheduled correctly
- `REQ_7` [behavior]: No dependencies produce lexicographic order
- `REQ_8` [behavior]: Smallest available task is selected first
- `REQ_9` [boundary]: Empty inputs return empty list
- `REQ_10` [boundary]: Single task returns single-element list
- `REQ_11` [behavior]: Independent chains use deterministic order
- `REQ_12` [behavior]: Diamond graph handled correctly
- `REQ_13` [error]: Duplicate tasks raise ValueError
- `REQ_14` [error]: Unknown dependency task raises ValueError
- `REQ_15` [error]: Circular dependency raises ValueError
- `REQ_16` [error]: Non-list tasks raises TypeError
- `REQ_17` [error]: Non-list dependencies raises TypeError
- `REQ_18` [error]: Non-string task name raises TypeError
- `REQ_19` [error]: Invalid dependency pair raises TypeError
- `REQ_20` [assumption]: Task names are case-sensitive

## Test Plan Trace

- `TP_1` -> REQ_1: Module exposes callable schedule_tasks
- `TP_2` -> REQ_2: Accepts tasks and dependencies inputs
- `TP_3` -> REQ_3: Returns list of task names
- `TP_4` -> REQ_4: Every task appears exactly once
- `TP_5` -> REQ_5: Dependencies are respected in order
- `TP_6` -> REQ_6: Linear chain scheduled correctly
- `TP_7` -> REQ_7: No dependencies produce lexicographic order
- `TP_8` -> REQ_8: Smallest available task is selected first
- `TP_9` -> REQ_9: Empty inputs return empty list
- `TP_10` -> REQ_10: Single task returns single-element list
- `TP_11` -> REQ_11: Independent chains use deterministic order
- `TP_12` -> REQ_12: Diamond graph handled correctly
- `TP_13` -> REQ_13: Duplicate tasks raise ValueError
- `TP_14` -> REQ_14: Unknown dependency task raises ValueError
- `TP_15` -> REQ_15: Circular dependency raises ValueError
- `TP_16` -> REQ_16: Non-list tasks raises TypeError
- `TP_17` -> REQ_17: Non-list dependencies raises TypeError
- `TP_18` -> REQ_18: Non-string task name raises TypeError
- `TP_19` -> REQ_19: Invalid dependency pair raises TypeError
- `TP_20` -> REQ_20: Task names are case-sensitive

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
