# task scheduler with dependencies

Generated Python project from an English software specification.

## Public API

- `schedule_tasks(tasks: list[str], dependencies: list[tuple[str, str]]) -> list[str]`: Computes a valid execution order for tasks with dependencies, returning an ordered list of tasks such that every task appears after all of its dependencies.

## Requirements

- `REQ_1` [api]: The function schedule_tasks must accept a parameter 'tasks' which is a list of unique task names (strings).
- `REQ_2` [api]: The function schedule_tasks must accept a parameter 'dependencies' which is a list of pairs of strings representing dependency pairs (before_task, after_task).
- `REQ_3` [api]: The function schedule_tasks must return a list of strings representing a valid ordering of all tasks.
- `REQ_4` [behavior]: Every task in the input 'tasks' list must appear exactly once in the returned execution order.
- `REQ_5` [behavior]: For every dependency pair (A, B), task A must appear before task B in the returned order.
- `REQ_6` [behavior]: The output ordering must be deterministic: when multiple tasks are available to schedule, the lexicographically smallest task is selected first.
- `REQ_7` [error]: If the 'tasks' list contains duplicate task names, schedule_tasks must raise a ValueError.
- `REQ_8` [error]: If any dependency refers to a task not present in the 'tasks' list, schedule_tasks must raise a ValueError.
- `REQ_9` [error]: If a circular dependency exists among tasks, schedule_tasks must raise a ValueError.
- `REQ_10` [error]: If the 'tasks' parameter is not a list, schedule_tasks must raise a TypeError.
- `REQ_11` [error]: If the 'dependencies' parameter is not a list, schedule_tasks must raise a TypeError.
- `REQ_12` [error]: If any task name in 'tasks' is not a string, schedule_tasks must raise a TypeError.
- `REQ_13` [error]: If any dependency is not a pair of strings, schedule_tasks must raise a TypeError.
- `REQ_14` [boundary]: If 'tasks' and 'dependencies' are both empty, schedule_tasks must return an empty list.
- `REQ_15` [boundary]: If there is a single task with no dependencies, schedule_tasks must return a list containing only that task.
- `REQ_16` [boundary]: If there are multiple tasks with no dependencies, schedule_tasks must return them in lexicographic order.
- `REQ_17` [boundary]: For a long dependency chain, schedule_tasks must return tasks in dependency order.
- `REQ_18` [boundary]: For multiple independent chains, schedule_tasks must produce a deterministic ordering based on lexicographic availability.
- `REQ_19` [boundary]: For a diamond-shaped dependency graph, schedule_tasks must return an ordering where downstream tasks appear after all their prerequisites.
- `REQ_20` [assumption]: Task names are case-sensitive.
- `REQ_21` [assumption]: The function schedule_tasks returns only the ordering and does not execute tasks or perform any file or external side effects.
- `REQ_22` [performance]: The expected time complexity of schedule_tasks is O((N + E) log N), where N is the number of tasks and E is the number of dependencies.
- `REQ_23` [performance]: The expected space complexity of schedule_tasks is O(N + E), where N is the number of tasks and E is the number of dependencies.

## Test Plan Trace

- `TP_1` -> REQ_1: schedule_tasks accepts a parameter 'tasks' which is a list of unique task names (strings).
- `TP_2` -> REQ_2: schedule_tasks accepts a parameter 'dependencies' which is a list of pairs of strings representing dependency pairs (before_task, after_task).
- `TP_3` -> REQ_3: schedule_tasks returns a list of strings representing a valid ordering of all tasks.
- `TP_4` -> REQ_4: Every task in the input 'tasks' list appears exactly once in the returned execution order.
- `TP_5` -> REQ_5: For every dependency pair (A, B), task A appears before task B in the returned order.
- `TP_6` -> REQ_6: The output ordering is deterministic: when multiple tasks are available, the lexicographically smallest is selected first.
- `TP_7` -> REQ_7: If the 'tasks' list contains duplicate task names, schedule_tasks raises a ValueError.
- `TP_8` -> REQ_8: If any dependency refers to a task not present in the 'tasks' list, schedule_tasks raises a ValueError.
- `TP_9` -> REQ_9: If a circular dependency exists among tasks, schedule_tasks raises a ValueError.
- `TP_10` -> REQ_10: If the 'tasks' parameter is not a list, schedule_tasks raises a TypeError.
- `TP_11` -> REQ_11: If the 'dependencies' parameter is not a list, schedule_tasks raises a TypeError.
- `TP_12` -> REQ_12: If any task name in 'tasks' is not a string, schedule_tasks raises a TypeError.
- `TP_13` -> REQ_13: If any dependency is not a pair of strings, schedule_tasks raises a TypeError.
- `TP_14` -> REQ_14: If 'tasks' and 'dependencies' are both empty, schedule_tasks returns an empty list.
- `TP_15` -> REQ_15: If there is a single task with no dependencies, schedule_tasks returns a list containing only that task.
- `TP_16` -> REQ_16: If there are multiple tasks with no dependencies, schedule_tasks returns them in lexicographic order.
- `TP_17` -> REQ_17: For a long dependency chain, schedule_tasks returns tasks in dependency order.
- `TP_18` -> REQ_18: For multiple independent chains, schedule_tasks produces a deterministic ordering based on lexicographic availability.
- `TP_19` -> REQ_19: For a diamond-shaped dependency graph, schedule_tasks returns an ordering where downstream tasks appear after all their prerequisites.
- `TP_20` -> REQ_20: Task names are case-sensitive.
- `TP_21` -> REQ_21: schedule_tasks returns only the ordering and does not execute tasks or perform any file or external side effects.
- `TP_22` -> REQ_22: schedule_tasks has expected time complexity O((N + E) log N), where N is number of tasks and E is number of dependencies.
- `TP_23` -> REQ_23: schedule_tasks has expected space complexity O(N + E), where N is number of tasks and E is number of dependencies.

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
