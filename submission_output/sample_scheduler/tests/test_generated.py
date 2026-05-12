import pytest

from task_scheduler import schedule_tasks


def test_tp_1_callable():
    """TP_1: Module exposes callable schedule_tasks."""
    assert callable(schedule_tasks)


def test_tp_2_accepts_inputs():
    """TP_2: Accepts tasks and dependencies inputs."""
    assert schedule_tasks(["a", "b"], [("a", "b")]) == ["a", "b"]


def test_tp_3_returns_list():
    """TP_3: Returns list of task names."""
    assert isinstance(schedule_tasks(["a"], []), list)


def test_tp_4_every_task_once():
    """TP_4: Every task appears exactly once."""
    assert schedule_tasks(["b", "a", "c"], []) == ["a", "b", "c"]


def test_tp_5_dependencies_respected():
    """TP_5: Dependencies are respected in order."""
    result = schedule_tasks(["a", "b", "c"], [("a", "c"), ("b", "c")])
    assert result.index("a") < result.index("c")
    assert result.index("b") < result.index("c")


def test_tp_6_linear_chain():
    """TP_6: Linear chain scheduled correctly."""
    assert schedule_tasks(["c", "b", "a"], [("a", "b"), ("b", "c")]) == ["a", "b", "c"]


def test_tp_7_no_dependencies_lexicographic():
    """TP_7: No dependencies produce lexicographic order."""
    assert schedule_tasks(["b", "a", "c"], []) == ["a", "b", "c"]


def test_tp_8_available_ordering():
    """TP_8: Smallest available task is selected first."""
    assert schedule_tasks(["a", "b", "c"], [("a", "c")]) == ["a", "b", "c"]


def test_tp_9_empty_inputs():
    """TP_9: Empty inputs return empty list."""
    assert schedule_tasks([], []) == []


def test_tp_10_single_task():
    """TP_10: Single task returns single-element list."""
    assert schedule_tasks(["only"], []) == ["only"]


def test_tp_11_independent_chains():
    """TP_11: Independent chains use deterministic order."""
    assert schedule_tasks(["d", "c", "b", "a"], [("a", "c"), ("b", "d")]) == ["a", "b", "c", "d"]


def test_tp_12_diamond_graph():
    """TP_12: Diamond graph handled correctly."""
    assert schedule_tasks(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]) == ["a", "b", "c", "d"]


def test_tp_13_duplicate_tasks():
    """TP_13: Duplicate tasks raise ValueError."""
    with pytest.raises(ValueError):
        schedule_tasks(["a", "a"], [])


def test_tp_14_unknown_dependency():
    """TP_14: Unknown dependency task raises ValueError."""
    with pytest.raises(ValueError):
        schedule_tasks(["a"], [("a", "b")])


def test_tp_15_circular_dependency():
    """TP_15: Circular dependency raises ValueError."""
    with pytest.raises(ValueError):
        schedule_tasks(["a", "b"], [("a", "b"), ("b", "a")])


def test_tp_16_tasks_type():
    """TP_16: Non-list tasks raises TypeError."""
    with pytest.raises(TypeError):
        schedule_tasks(("a",), [])


def test_tp_17_dependencies_type():
    """TP_17: Non-list dependencies raises TypeError."""
    with pytest.raises(TypeError):
        schedule_tasks(["a"], ())


def test_tp_18_task_name_type():
    """TP_18: Non-string task name raises TypeError."""
    with pytest.raises(TypeError):
        schedule_tasks(["a", 1], [])


def test_tp_19_dependency_pair_type():
    """TP_19: Invalid dependency pair raises TypeError."""
    with pytest.raises(TypeError):
        schedule_tasks(["a"], [("a",)])


def test_tp_20_case_sensitive():
    """TP_20: Task names are case-sensitive."""
    assert schedule_tasks(["a", "A"], []) == ["A", "a"]

