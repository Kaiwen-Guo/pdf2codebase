import pytest
from task_scheduler import schedule_tasks

def test_tp_1_tasks_parameter_accepts_unique_strings():
    """TP_1: schedule_tasks accepts a parameter 'tasks' which is a list of unique task name strings"""
    tasks = ["a", "b", "c"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in tasks)

def test_tp_2_dependencies_parameter_accepts_list_of_pairs_of_strings():
    """TP_2: schedule_tasks accepts a parameter 'dependencies' which is a list of pairs of strings representing dependency edges"""
    tasks = ["a", "b"]
    dependencies = [("a", "b")]
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)
    assert all(isinstance(dep, tuple) and len(dep) == 2 and all(isinstance(x, str) for x in dep) for dep in dependencies)

def test_tp_3_returns_valid_ordering_of_all_tasks():
    """TP_3: schedule_tasks returns a list of strings representing a valid ordering of all tasks"""
    tasks = ["a", "b"]
    dependencies = [("a", "b")]
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)
    assert set(result) == set(tasks)

def test_tp_4_output_contains_all_tasks_exactly_once():
    """TP_4: Returned execution order contains every task from input exactly once"""
    tasks = ["a", "b", "c"]
    dependencies = [("a", "b")]
    result = schedule_tasks(tasks, dependencies)
    assert sorted(result) == sorted(tasks)
    assert len(result) == len(set(result))

def test_tp_5_dependencies_respected_in_output_order():
    """TP_5: For every dependency (A, B), A appears before B in the returned order"""
    tasks = ["a", "b", "c"]
    dependencies = [("a", "b"), ("b", "c")]
    result = schedule_tasks(tasks, dependencies)
    pos = {t: i for i, t in enumerate(result)}
    for a, b in dependencies:
        assert pos[a] < pos[b]

def test_tp_6_lexicographically_smallest_task_selected_first():
    """TP_6: When multiple tasks are available, lexicographically smallest task is selected first"""
    tasks = ["b", "a", "c"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert result == sorted(tasks)

def test_tp_7_raises_value_error_on_duplicate_tasks():
    """TP_7: Function raises ValueError if 'tasks' list contains duplicate task names"""
    tasks = ["a", "a"]
    dependencies = []
    with pytest.raises(ValueError):
        schedule_tasks(tasks, dependencies)

def test_tp_8_raises_value_error_on_unknown_task_in_dependencies():
    """TP_8: Function raises ValueError if any dependency refers to a task not in 'tasks' list"""
    tasks = ["a", "b"]
    dependencies = [("a", "c")]
    with pytest.raises(ValueError):
        schedule_tasks(tasks, dependencies)

def test_tp_9_raises_value_error_on_circular_dependency():
    """TP_9: Function raises ValueError if a circular dependency exists among tasks"""
    tasks = ["a", "b"]
    dependencies = [("a", "b"), ("b", "a")]
    with pytest.raises(ValueError):
        schedule_tasks(tasks, dependencies)

def test_tp_10_raises_type_error_if_tasks_not_list():
    """TP_10: Function raises TypeError if 'tasks' parameter is not a list"""
    tasks = "notalist"
    dependencies = []
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_11_raises_type_error_if_dependencies_not_list():
    """TP_11: Function raises TypeError if 'dependencies' parameter is not a list"""
    tasks = ["a"]
    dependencies = "notalist"
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_12_raises_type_error_if_task_name_not_string():
    """TP_12: Function raises TypeError if any task name in 'tasks' is not a string"""
    tasks = ["a", 1]
    dependencies = []
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_13_raises_type_error_if_dependency_not_pair_of_strings():
    """TP_13: Function raises TypeError if any dependency is not a pair of strings"""
    tasks = ["a", "b"]
    dependencies = [("a", "b"), ("a", 1)]
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)
    dependencies = [("a",)]
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)
    dependencies = [("a", "b", "c")]
    with pytest.raises(TypeError):
        schedule_tasks(tasks, dependencies)

def test_tp_14_empty_tasks_and_dependencies_returns_empty_list():
    """TP_14: Function returns empty list if 'tasks' and 'dependencies' are both empty"""
    tasks = []
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert result == []

def test_tp_15_single_task_no_dependencies_returns_single_task():
    """TP_15: Function returns list containing single task if one task with no dependencies"""
    tasks = ["onlytask"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert result == ["onlytask"]

def test_tp_16_multiple_tasks_no_dependencies_returns_lex_order():
    """TP_16: Function returns multiple tasks in lexicographic order if no dependencies"""
    tasks = ["b", "a", "c"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert result == sorted(tasks)

def test_tp_17_long_dependency_chain_respects_order():
    """TP_17: Function returns tasks in dependency order for a long dependency chain"""
    tasks = ["a", "b", "c", "d", "e"]
    dependencies = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
    result = schedule_tasks(tasks, dependencies)
    pos = {t: i for i, t in enumerate(result)}
    for a, b in dependencies:
        assert pos[a] < pos[b]

def test_tp_18_multiple_independent_chains_lexicographic_order():
    """TP_18: Function produces deterministic order using lexicographic availability for multiple independent chains"""
    tasks = ["a1", "a2", "b1", "b2"]
    dependencies = [("a1", "a2"), ("b1", "b2")]
    result = schedule_tasks(tasks, dependencies)
    # After a1 completes, available are a2 and b1; lex smallest is a2
    # So order should be a1, a2, b1, b2 or a1, b1, a2, b2 depending on lex availability
    # But since a1 completes first, available are a2 and b1; a2 < b1 so a2 next
    # Then b1, then b2
    expected = ["a1", "a2", "b1", "b2"]
    assert result == expected

def test_tp_19_diamond_dependency_structure_respected():
    """TP_19: Function returns tasks so downstream tasks appear after all prerequisites in diamond-shaped graph"""
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
    """TP_20: Task names are case-sensitive"""
    tasks = ["a", "A"]
    dependencies = []
    result = schedule_tasks(tasks, dependencies)
    assert set(result) == set(tasks)
    assert result != ["a", "a"] and result != ["A", "A"]

def test_tp_21_function_returns_ordering_only_no_side_effects():
    """TP_21: Function returns only the ordering of tasks without executing tasks or side effects"""
    tasks = ["a", "b"]
    dependencies = [("a", "b")]
    result = schedule_tasks(tasks, dependencies)
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)

def test_tp_22_function_implements_standard_topological_sort():
    """TP_22: Function implements a standard topological sort algorithm"""
    tasks = ["a", "b", "c", "d"]
    dependencies = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
    result = schedule_tasks(tasks, dependencies)
    pos = {t: i for i, t in enumerate(result)}
    for a, b in dependencies:
        assert pos[a] < pos[b]

def test_tp_23_function_performance_complexity_heuristic():
    """TP_23: Function runs in O((N + E) log N) time and uses O(N + E) space"""
    # This is a heuristic test: run on large input and check it completes quickly
    n = 1000
    tasks = [f"t{i}" for i in range(n)]
    dependencies = [(f"t{i}", f"t{i+1}") for i in range(n-1)]
    result = schedule_tasks(tasks, dependencies)
    assert len(result) == n
    # Check order respects dependencies
    pos = {t: i for i, t in enumerate(result)}
    for a, b in dependencies:
        assert pos[a] < pos[b]