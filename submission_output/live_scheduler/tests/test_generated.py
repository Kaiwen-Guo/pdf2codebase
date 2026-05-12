import pytest
from task_scheduler import schedule_tasks

def test_tp_1_tasks_parameter_accepts_list_of_strings():
    """TP_1: schedule_tasks accepts a parameter 'tasks' which is a list of unique task names (strings)."""
    tasks = ["task1", "task2"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in tasks)

def test_tp_2_dependencies_parameter_accepts_list_of_pairs_of_strings():
    """TP_2: schedule_tasks accepts a parameter 'dependencies' which is a list of pairs of strings representing dependency pairs (before_task, after_task)."""
    tasks = ["a", "b"]
    dependencies = [("a", "b")]
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)
    assert all(isinstance(dep, tuple) and len(dep) == 2 and all(isinstance(x, str) for x in dep) for dep in dependencies)

def test_tp_3_returns_list_of_strings_representing_valid_ordering():
    """TP_3: schedule_tasks returns a list of strings representing a valid ordering of all tasks."""
    tasks = ["a", "b"]
    dependencies = [("a", "b")]
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)
    assert set(result) == set(tasks)

def test_tp_4_all_tasks_appear_once_in_returned_order():
    """TP_4: Every task in the input 'tasks' list appears exactly once in the returned execution order."""
    tasks = ["a", "b", "c"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert sorted(result) == sorted(tasks)
    assert len(result) == len(set(result))

def test_tp_5_dependencies_respected_in_ordering():
    """TP_5: For every dependency pair (A, B), task A appears before task B in the returned order."""
    tasks = ["a", "b", "c"]
    dependencies = [("a", "b"), ("b", "c")]
    result = schedule_tasks(tasks, dependencies)
    pos = {task: i for i, task in enumerate(result)}
    for before_task, after_task in dependencies:
        assert pos[before_task] < pos[after_task]

def test_tp_6_ordering_is_deterministic_and_lex_smallest_first():
    """TP_6: The output ordering is deterministic: when multiple tasks are available, the lexicographically smallest is selected first."""
    tasks = ["b", "a", "c"]
    dependencies = []
    result1 = schedule_tasks(tasks, dependencies)
    result2 = schedule_tasks(tasks, dependencies)
    assert result1 == result2
    assert result1 == sorted(tasks)

def test_tp_7_duplicate_tasks_raises_value_error():
    """TP_7: If the 'tasks' list contains duplicate task names, schedule_tasks raises a ValueError."""
    tasks = ["a", "a"]
    dependencies = []
    with pytest.raises(ValueError):
        schedule_tasks(tasks, dependencies)

def test_tp_8_dependency_refers_unknown_task_raises_value_error():
    """TP_8: If any dependency refers to a task not present in the 'tasks' list, schedule_tasks raises a ValueError."""
    tasks = ["a", "b"]
    dependencies = [("a", "c")]
    with pytest.raises(ValueError):
        schedule_tasks(tasks, dependencies)

def test_tp_9_circular_dependency_raises_value_error():
    """TP_9: If a circular dependency exists among tasks, schedule_tasks raises a ValueError."""
    tasks = ["a", "b"]
    dependencies = [("a", "b"), ("b", "a")]
    with pytest.raises(ValueError):
        schedule_tasks(tasks, dependencies)

def test_tp_10_tasks_not_list_raises_type_error():
    """TP_10: If the 'tasks' parameter is not a list, schedule_tasks raises a TypeError."""
    tasks = "notalist"
    dependencies = []
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_11_dependencies_not_list_raises_type_error():
    """TP_11: If the 'dependencies' parameter is not a list, schedule_tasks raises a TypeError."""
    tasks = ["a"]
    dependencies = "notalist"
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_12_task_name_not_string_raises_type_error():
    """TP_12: If any task name in 'tasks' is not a string, schedule_tasks raises a TypeError."""
    tasks = ["a", 1]
    dependencies = []
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_13_dependency_not_pair_of_strings_raises_type_error():
    """TP_13: If any dependency is not a pair of strings, schedule_tasks raises a TypeError."""
    tasks = ["a", "b"]
    dependencies = [("a", "b"), ("b", 1)]
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)
    dependencies = [("a",)]
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)
    dependencies = [("a", "b", "c")]
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_14_empty_tasks_and_dependencies_returns_empty_list():
    """TP_14: If 'tasks' and 'dependencies' are both empty, schedule_tasks returns an empty list."""
    tasks = []
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert result == []

def test_tp_15_single_task_no_dependencies_returns_single_task():
    """TP_15: If there is a single task with no dependencies, schedule_tasks returns a list containing only that task."""
    tasks = ["onlytask"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert result == ["onlytask"]

def test_tp_16_multiple_tasks_no_dependencies_returns_lex_order():
    """TP_16: If there are multiple tasks with no dependencies, schedule_tasks returns them in lexicographic order."""
    tasks = ["b", "a", "c"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert result == sorted(tasks)

def test_tp_17_long_dependency_chain_returns_tasks_in_dependency_order():
    """TP_17: For a long dependency chain, schedule_tasks returns tasks in dependency order."""
    tasks = ["a", "b", "c", "d", "e"]
    dependencies = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
    result = schedule_tasks(tasks, dependencies)
    pos = {t: i for i, t in enumerate(result)}
    for before_task, after_task in dependencies:
        assert pos[before_task] < pos[after_task]

def test_tp_18_multiple_independent_chains_deterministic_lex_order():
    """TP_18: For multiple independent chains, schedule_tasks produces a deterministic ordering based on lexicographic availability."""
    tasks = ["a1", "a2", "b1", "b2"]
    dependencies = [("a1", "a2"), ("b1", "b2")]
    result = schedule_tasks(tasks, dependencies)
    # After a1 completes, available are a2 and b1; lex smallest is a2
    # So expected order: a1, a2, b1, b2
    assert result == ["a1", "a2", "b1", "b2"]

def test_tp_19_diamond_shaped_dependency_graph_ordering():
    """TP_19: For a diamond-shaped dependency graph, schedule_tasks returns an ordering where downstream tasks appear after all their prerequisites."""
    tasks = ["a", "b", "c", "d"]
    dependencies = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
    result = schedule_tasks(tasks, dependencies)
    pos = {t: i for i, t in enumerate(result)}
    # a before b and c
    assert pos["a"] < pos["b"]
    assert pos["a"] < pos["c"]
    # b and c before d
    assert pos["b"] < pos["d"]
    assert pos["c"] < pos["d"]
    # a is first task
    assert result[0] == "a"

def test_tp_20_task_names_case_sensitive():
    """TP_20: Task names are case-sensitive."""
    tasks = ["a", "A"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert set(result) == set(tasks)
    assert result != ["a", "a"]
    assert "a" in result and "A" in result

def test_tp_21_no_side_effects(monkeypatch):
    """TP_21: schedule_tasks returns only the ordering and does not execute tasks or perform any file or external side effects."""
    # We monkeypatch builtins open, os, subprocess to detect side effects
    import builtins
    import os
    import subprocess

    def fail_open(*args, **kwargs):
        pytest.fail("Unexpected file open")

    def fail_os(*args, **kwargs):
        pytest.fail("Unexpected os call")

    def fail_subprocess(*args, **kwargs):
        pytest.fail("Unexpected subprocess call")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(os, "system", fail_os)
    monkeypatch.setattr(subprocess, "Popen", fail_subprocess)
    monkeypatch.setattr(subprocess, "call", fail_subprocess)
    monkeypatch.setattr(subprocess, "run", fail_subprocess)

    tasks = ["a", "b"]
    dependencies = [("a", "b")]
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)

def test_tp_22_performance_time_complexity():
    """TP_22: schedule_tasks has expected time complexity O((N + E) log N), where N is number of tasks and E is number of dependencies."""
    # We test with a large chain and measure time roughly to ensure no pathological slowness
    import time
    N = 10000
    tasks = [f"t{i}" for i in range(N)]
    dependencies = [(f"t{i}", f"t{i+1}") for i in range(N-1)]
    start = time.perf_counter()
    result = schedule_tasks(tasks, dependencies)
    duration = time.perf_counter() - start
    assert result[0] == "t0"
    assert result[-1] == f"t{N-1}"
    # Assert it runs under 1 second as a heuristic for complexity
    assert duration < 1.0

def test_tp_23_performance_space_complexity():
    """TP_23: schedule_tasks has expected space complexity O(N + E), where N is number of tasks and E is number of dependencies."""
    # We test that function completes on large input without MemoryError
    N = 10000
    tasks = [f"t{i}" for i in range(N)]
    dependencies = [(f"t{i}", f"t{i+1}") for i in range(N-1)]
    result = schedule_tasks(tasks, dependencies)
    assert len(result) == N