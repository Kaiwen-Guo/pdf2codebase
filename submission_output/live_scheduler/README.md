# task scheduler with dependencies

Generated Python project from an English software specification.

## Public API

- `schedule_tasks(tasks: list[str], dependencies: list[tuple[str, str]]) -> list[str]`: Computes a valid execution order for tasks with dependencies, returning an ordered list of tasks such that every task appears after all of its dependencies.

## Requirements

- `REQ_1` [api]: The function schedule_tasks must accept a parameter 'tasks' which is a list of unique task name strings.
- `REQ_2` [api]: The function schedule_tasks must accept a parameter 'dependencies' which is a list of pairs of strings representing dependency edges (before_task, after_task).
- `REQ_3` [api]: The function schedule_tasks returns a list of strings representing a valid ordering of all tasks.
- `REQ_4` [behavior]: Every task in the input 'tasks' list must appear exactly once in the returned execution order.
- `REQ_5` [behavior]: For every dependency pair (A, B), task A must appear before task B in the returned order.
- `REQ_6` [behavior]: When multiple tasks are available to schedule, the lexicographically smallest task must be selected first to ensure deterministic output.
- `REQ_7` [error]: If the 'tasks' list contains duplicate task names, the function must raise a ValueError.
- `REQ_8` [error]: If any dependency refers to a task not present in the 'tasks' list, the function must raise a ValueError.
- `REQ_9` [error]: If a circular dependency exists among tasks, the function must raise a ValueError.
- `REQ_10` [error]: If the 'tasks' parameter is not a list, the function must raise a TypeError.
- `REQ_11` [error]: If the 'dependencies' parameter is not a list, the function must raise a TypeError.
- `REQ_12` [error]: If any task name in 'tasks' is not a string, the function must raise a TypeError.
- `REQ_13` [error]: If any dependency is not a pair of strings, the function must raise a TypeError.
- `REQ_14` [boundary]: If 'tasks' and 'dependencies' are both empty, the function must return an empty list.
- `REQ_15` [boundary]: If there is a single task with no dependencies, the function must return a list containing only that task.
- `REQ_16` [boundary]: If there are multiple tasks with no dependencies, the function must return them in lexicographic order.
- `REQ_17` [boundary]: For a long dependency chain, the function must return tasks in dependency order.
- `REQ_18` [boundary]: For multiple independent chains, the function must produce a deterministic order using lexicographic availability.
- `REQ_19` [boundary]: For a diamond-shaped dependency graph, the function must return tasks so that downstream tasks appear after all their prerequisites.
- `REQ_20` [assumption]: Task names are case-sensitive.
- `REQ_21` [assumption]: The function returns only the ordering of tasks and does not execute tasks or perform any file or external side effects.
- `REQ_22` [assumption]: The function must implement a standard topological sort algorithm.
- `REQ_23` [performance]: The function must run in O((N + E) log N) time and use O(N + E) space, where N is the number of tasks and E is the number of dependencies.

## Test Plan Trace

- `TP_1` -> REQ_1: schedule_tasks accepts a parameter 'tasks' which is a list of unique task name strings
- `TP_2` -> REQ_2: schedule_tasks accepts a parameter 'dependencies' which is a list of pairs of strings representing dependency edges
- `TP_3` -> REQ_3: schedule_tasks returns a list of strings representing a valid ordering of all tasks
- `TP_4` -> REQ_4: Returned execution order contains every task from input exactly once
- `TP_5` -> REQ_5: For every dependency (A, B), A appears before B in the returned order
- `TP_6` -> REQ_6: When multiple tasks are available, lexicographically smallest task is selected first
- `TP_7` -> REQ_7: Function raises ValueError if 'tasks' list contains duplicate task names
- `TP_8` -> REQ_8: Function raises ValueError if any dependency refers to a task not in 'tasks' list
- `TP_9` -> REQ_9: Function raises ValueError if a circular dependency exists among tasks
- `TP_10` -> REQ_10: Function raises TypeError if 'tasks' parameter is not a list
- `TP_11` -> REQ_11: Function raises TypeError if 'dependencies' parameter is not a list
- `TP_12` -> REQ_12: Function raises TypeError if any task name in 'tasks' is not a string
- `TP_13` -> REQ_13: Function raises TypeError if any dependency is not a pair of strings
- `TP_14` -> REQ_14: Function returns empty list if 'tasks' and 'dependencies' are both empty
- `TP_15` -> REQ_15: Function returns list containing single task if one task with no dependencies
- `TP_16` -> REQ_16: Function returns multiple tasks in lexicographic order if no dependencies
- `TP_17` -> REQ_17: Function returns tasks in dependency order for a long dependency chain
- `TP_18` -> REQ_18: Function produces deterministic order using lexicographic availability for multiple independent chains
- `TP_19` -> REQ_19: Function returns tasks so downstream tasks appear after all prerequisites in diamond-shaped graph
- `TP_20` -> REQ_20: Task names are case-sensitive
- `TP_21` -> REQ_21: Function returns only the ordering of tasks without executing tasks or side effects
- `TP_22` -> REQ_22: Function implements a standard topological sort algorithm
- `TP_23` -> REQ_23: Function runs in O((N + E) log N) time and uses O(N + E) space

## Run

```bash
PYTHONPATH=generated python main.py
PYTHONPATH=generated python -m pytest -q tests/test_generated.py
```

## Generated Layout

```text
generated/          # generated source modules
tests/              # generated pytest suite
project_spec.json   # normalized requirements and public APIs
test_plan.json      # executable test-plan items
codebase_manifest.json
```
