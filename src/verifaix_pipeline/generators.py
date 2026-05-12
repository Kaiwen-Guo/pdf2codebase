from __future__ import annotations

import json
import re
import warnings

from .llm import LLMClient, compose_prompt, strip_markdown_fence
from .models import (
    CodebaseManifest,
    Delta,
    GeneratedFile,
    ProjectSpec,
    PublicAPI,
    Requirement,
    TestPlan,
    TestPlanItem,
)


def infer_module_name(description_text: str, configured_name: str) -> str:
    if "schedule_tasks" in description_text:
        return "task_scheduler"
    return configured_name


def generate_project_spec(
    description_text: str,
    llm_client: LLMClient,
    use_llm: bool,
    fallback_to_deterministic: bool,
) -> tuple[ProjectSpec, str]:
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/response_discipline.txt",
            "blueprints/project_spec_schema.txt",
            "blueprints/traceability.txt",
            "skills/spec_extractor.txt",
        ],
        description_text=description_text,
    )
    if use_llm and llm_client.enabled:
        try:
            return ProjectSpec.from_dict(llm_client.generate_json(prompt)), prompt
        except Exception as exc:
            if not fallback_to_deterministic:
                raise
            warnings.warn(
                f"LLM project-spec generation failed; using deterministic fallback: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
    return deterministic_project_spec(description_text), prompt


def generate_test_plan(
    description_text: str,
    project_spec: ProjectSpec,
    llm_client: LLMClient,
    use_llm: bool,
    fallback_to_deterministic: bool,
) -> tuple[TestPlan, str]:
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/response_discipline.txt",
            "blueprints/test_plan_schema.txt",
            "blueprints/traceability.txt",
            "skills/test_plan_generator.txt",
        ],
        description_text=description_text,
        project_spec_json=json.dumps(project_spec.to_dict(), indent=2),
    )
    if use_llm and llm_client.enabled:
        try:
            test_plan = TestPlan.from_dict(llm_client.generate_json(prompt))
            return ensure_requirement_ids_covered(project_spec, test_plan), prompt
        except Exception as exc:
            if not fallback_to_deterministic:
                raise
            warnings.warn(
                f"LLM test-plan generation failed; using deterministic fallback: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
    return deterministic_test_plan(description_text), prompt


def ensure_requirement_ids_covered(
    project_spec: ProjectSpec,
    test_plan: TestPlan,
) -> TestPlan:
    covered = {
        req_id
        for item in test_plan.items
        for req_id in item.requirement_ids
    }
    missing = [
        requirement
        for requirement in project_spec.requirements
        if requirement.req_id not in covered
    ]
    if not missing:
        return test_plan

    items = list(test_plan.items)
    next_index = _next_tp_index(items)
    for requirement in missing:
        items.append(
            TestPlanItem(
                tp_id=f"TP_{next_index}",
                description=requirement.description,
                source_sections=requirement.source_sections,
                expected_behavior=requirement.description,
                category=requirement.category,
                requirement_ids=[requirement.req_id],
            )
        )
        next_index += 1
    return TestPlan(items)


def _next_tp_index(items: list[TestPlanItem]) -> int:
    indexes: list[int] = []
    for item in items:
        match = re.search(r"(\d+)", item.tp_id)
        if match:
            indexes.append(int(match.group(1)))
    return (max(indexes) + 1) if indexes else 1


def generate_codebase(
    project_spec: ProjectSpec,
    test_plan: TestPlan,
    llm_client: LLMClient,
    use_llm: bool,
    fallback_to_deterministic: bool,
) -> tuple[CodebaseManifest, str]:
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/response_discipline.txt",
            "blueprints/code_contract.txt",
            "blueprints/codebase_manifest_schema.txt",
            "blueprints/traceability.txt",
            "skills/codebase_generator.txt",
        ],
        project_spec_json=json.dumps(project_spec.to_dict(), indent=2),
        test_plan_json=json.dumps(test_plan.to_dict(), indent=2),
    )
    if use_llm and llm_client.enabled:
        try:
            return CodebaseManifest.from_dict(llm_client.generate_json(prompt)), prompt
        except Exception as exc:
            if not fallback_to_deterministic:
                raise
            warnings.warn(
                f"LLM codebase generation failed; using deterministic fallback: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
    deterministic_hint = "schedule_tasks" if project_spec.module_name == "task_scheduler" else ""
    source = deterministic_code(deterministic_hint, project_spec.module_name)
    return (
        CodebaseManifest(
            entry_module=project_spec.module_name,
            files=[
                GeneratedFile(
                    path=f"{project_spec.module_name}.py",
                    kind="source",
                    purpose="implementation",
                    content=source,
                )
            ],
        ),
        prompt,
    )


def repair_codebase(
    project_spec: ProjectSpec,
    test_plan: TestPlan,
    manifest: CodebaseManifest,
    failure_output: str,
    llm_client: LLMClient,
) -> tuple[CodebaseManifest, str]:
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/response_discipline.txt",
            "blueprints/code_contract.txt",
            "blueprints/codebase_manifest_schema.txt",
            "blueprints/pytest_contract.txt",
            "blueprints/traceability.txt",
            "skills/repair_generator.txt",
        ],
        project_spec_json=json.dumps(project_spec.to_dict(), indent=2),
        test_plan_json=json.dumps(test_plan.to_dict(), indent=2),
        codebase_manifest_json=json.dumps(manifest.to_dict(), indent=2),
        failure_output=failure_output,
    )
    return CodebaseManifest.from_dict(llm_client.generate_json(prompt)), prompt


def generate_code(
    description_text: str,
    test_plan: TestPlan,
    module_name: str,
    llm_client: LLMClient,
    use_llm: bool,
    fallback_to_deterministic: bool,
) -> tuple[str, str]:
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/response_discipline.txt",
            "blueprints/code_contract.txt",
            "blueprints/traceability.txt",
            "skills/code_generator.txt",
        ],
        description_text=description_text,
        test_plan_json=json.dumps(test_plan.to_dict(), indent=2),
    )
    if use_llm and llm_client.enabled:
        try:
            return strip_markdown_fence(llm_client.generate_text(prompt)), prompt
        except Exception as exc:
            if not fallback_to_deterministic:
                raise
            warnings.warn(
                f"LLM code generation failed; using deterministic fallback: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
    return deterministic_code(description_text, module_name), prompt


def generate_tests(
    description_text: str,
    test_plan: TestPlan,
    module_name: str,
    llm_client: LLMClient,
    use_llm: bool,
    fallback_to_deterministic: bool,
) -> tuple[str, str]:
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/response_discipline.txt",
            "blueprints/pytest_contract.txt",
            "blueprints/traceability.txt",
            "skills/pytest_generator.txt",
        ],
        module_name=module_name,
        description_text=description_text,
        test_plan_json=json.dumps(test_plan.to_dict(), indent=2),
    )
    if use_llm and llm_client.enabled:
        try:
            return strip_markdown_fence(llm_client.generate_text(prompt)), prompt
        except Exception as exc:
            if not fallback_to_deterministic:
                raise
            warnings.warn(
                f"LLM test generation failed; using deterministic fallback: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
    return deterministic_tests(description_text, module_name), prompt


def compare_test_plans(old_plan: TestPlan, new_plan: TestPlan) -> list[Delta]:
    old_by_id = {item.tp_id: item for item in old_plan.items}
    new_by_id = {item.tp_id: item for item in new_plan.items}
    deltas: list[Delta] = []
    next_id = 1

    for tp_id in sorted(new_by_id, key=_tp_sort_key):
        if tp_id not in old_by_id:
            deltas.append(
                Delta(f"D_{next_id}", "Added", tp_id, new_by_id[tp_id].description)
            )
            next_id += 1
        elif _item_signature(old_by_id[tp_id]) != _item_signature(new_by_id[tp_id]):
            deltas.append(
                Delta(f"D_{next_id}", "Modified", tp_id, new_by_id[tp_id].description)
            )
            next_id += 1

    for tp_id in sorted(old_by_id, key=_tp_sort_key):
        if tp_id not in new_by_id:
            deltas.append(
                Delta(f"D_{next_id}", "Removed", tp_id, old_by_id[tp_id].description)
            )
            next_id += 1

    return deltas


def generate_deltas(
    old_plan: TestPlan,
    new_plan: TestPlan,
    llm_client: LLMClient,
    use_llm: bool,
    fallback_to_deterministic: bool,
    old_description_text: str = "",
    new_description_text: str = "",
) -> tuple[list[Delta], str]:
    prompt = compose_prompt(
        [
            "blueprints/system_context.txt",
            "blueprints/response_discipline.txt",
            "blueprints/delta_schema.txt",
            "blueprints/traceability.txt",
            "skills/delta_analyzer.txt",
        ],
        old_description_text=old_description_text,
        new_description_text=new_description_text,
        old_test_plan_json=json.dumps(old_plan.to_dict(), indent=2),
        new_test_plan_json=json.dumps(new_plan.to_dict(), indent=2),
    )
    if use_llm and llm_client.enabled:
        try:
            raw = llm_client.generate_json(prompt)
            deltas = [
                Delta(
                    delta_id=str(item["delta_id"]),
                    change_type=str(item["change_type"]),
                    tp_id=str(item["tp_id"]),
                    description=str(item["description"]),
                )
                for item in raw.get("deltas", [])
            ]
            return filter_deltas_against_descriptions(
                clean_deltas(deltas), old_description_text, new_description_text
            ), prompt
        except Exception as exc:
            if not fallback_to_deterministic:
                raise
            warnings.warn(
                f"LLM delta generation failed; using structural fallback: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
    return filter_deltas_against_descriptions(
        clean_deltas(compare_test_plans(old_plan, new_plan)),
        old_description_text,
        new_description_text,
    ), prompt


def clean_deltas(deltas: list[Delta]) -> list[Delta]:
    allowed_types = {"Added", "Removed", "Modified"}
    noise_terms = (
        "clarified",
        "renamed",
        "renumbered",
        "reworded",
        "merged",
        "wording-only",
        "unchanged",
        "included for completeness",
        "adjusted id",
        "new tp_",
    )
    cleaned: list[Delta] = []
    seen_delta_ids: set[str] = set()
    seen_tp_ids: set[str] = set()
    next_id = 1
    for delta in deltas:
        change_type = delta.change_type.strip().title()
        if change_type not in allowed_types:
            continue
        description = delta.description.strip()
        if not delta.tp_id.strip() or not description:
            continue
        lowered = description.lower()
        if any(term in lowered for term in noise_terms):
            continue
        if delta.delta_id in seen_delta_ids or delta.tp_id in seen_tp_ids:
            continue
        seen_delta_ids.add(delta.delta_id)
        seen_tp_ids.add(delta.tp_id)
        cleaned.append(Delta(f"D_{next_id}", change_type, delta.tp_id, description))
        next_id += 1
    return cleaned


def filter_deltas_against_descriptions(
    deltas: list[Delta],
    old_description_text: str,
    new_description_text: str,
) -> list[Delta]:
    old_lower = old_description_text.lower()
    new_lower = new_description_text.lower()
    filtered: list[Delta] = []
    next_id = 1
    for delta in deltas:
        description = delta.description.lower()
        if "complexity" in description and "complexity" in old_lower and "complexity" in new_lower:
            continue
        filtered.append(
            Delta(f"D_{next_id}", delta.change_type, delta.tp_id, delta.description)
        )
        next_id += 1
    return filtered


def deterministic_test_plan(description_text: str) -> TestPlan:
    if "schedule_tasks" not in description_text:
        raise RuntimeError(
            "Deterministic fallback only supports the sample task scheduler spec"
        )
    reverse = "reverse" in description_text and "largest available" in description_text
    items = [
        item("TP_1", "Module exposes callable schedule_tasks", ["1.1"], "schedule_tasks can be imported and called", "api"),
        item("TP_2", "Accepts tasks and dependencies inputs", ["1.1"], "Function accepts tasks and dependency pairs", "api"),
        item("TP_3", "Returns list of task names", ["1.1"], "Return value is a list", "api"),
        item("TP_4", "Every task appears exactly once", ["1.2"], "Output contains each input task exactly once", "behavior"),
        item("TP_5", "Dependencies are respected in order", ["1.2"], "Every before task appears before its after task", "behavior"),
        item("TP_6", "Linear chain scheduled correctly", ["1.1", "1.4"], "Long dependency chains are ordered correctly", "boundary"),
        item("TP_7", "No dependencies produce lexicographic order", ["1.2", "1.4"], "Independent tasks are sorted lexicographically", "behavior"),
        item("TP_8", "Smallest available task is selected first", ["1.2", "1.5"], "Among ready tasks, the smallest task name is selected first", "behavior"),
        item("TP_9", "Empty inputs return empty list", ["1.4"], "Empty tasks and dependencies return []", "boundary"),
        item("TP_10", "Single task returns single-element list", ["1.4"], "A single task is returned as a one-item list", "boundary"),
        item("TP_11", "Independent chains use deterministic order", ["1.4"], "Multiple chains are interleaved by lexicographic availability", "behavior"),
        item("TP_12", "Diamond graph handled correctly", ["1.4"], "Downstream task appears after all prerequisites", "behavior"),
        item("TP_13", "Duplicate tasks raise ValueError", ["1.3"], "Duplicate task names are rejected", "error"),
        item("TP_14", "Unknown dependency task raises ValueError", ["1.3"], "Dependencies referencing missing tasks are rejected", "error"),
        item("TP_15", "Circular dependency raises ValueError", ["1.3"], "Cycles are rejected", "error"),
        item("TP_16", "Non-list tasks raises TypeError", ["1.3"], "tasks must be a list", "error"),
        item("TP_17", "Non-list dependencies raises TypeError", ["1.3"], "dependencies must be a list", "error"),
        item("TP_18", "Non-string task name raises TypeError", ["1.3"], "task names must be strings", "error"),
        item("TP_19", "Invalid dependency pair raises TypeError", ["1.3"], "dependencies must be pairs of strings", "error"),
        item("TP_20", "Task names are case-sensitive", ["1.5"], "Distinct case variants are separate tasks", "assumption"),
    ]
    if reverse:
        items[7] = item("TP_8", "Ordering honors reverse parameter when choosing available tasks", ["1.2", "1.5"], "reverse controls smallest versus largest ready task", "behavior")
        items.extend(
            [
                item("TP_21", "Accepts optional reverse parameter", ["4"], "schedule_tasks accepts reverse=False by default", "api"),
                item("TP_22", "Default reverse is False", ["4"], "Omitting reverse keeps lexicographically smallest-first ordering", "behavior"),
                item("TP_23", "reverse=False selects smallest available task first", ["4"], "Explicit reverse=False matches default behavior", "behavior"),
                item("TP_24", "reverse=True selects largest available task first", ["4"], "reverse=True chooses the largest ready task first", "behavior"),
            ]
        )
    return TestPlan(items)


def deterministic_project_spec(description_text: str) -> ProjectSpec:
    if "schedule_tasks" not in description_text:
        raise RuntimeError(
            "Deterministic fallback only supports the sample task scheduler spec"
        )
    plan = deterministic_test_plan(description_text)
    requirements = [
        Requirement(
            req_id=f"REQ_{index}",
            description=item.description,
            category=item.category,
            source_sections=item.source_sections,
        )
        for index, item in enumerate(plan.items, start=1)
    ]
    return ProjectSpec(
        project_name="Task Scheduler",
        module_name="task_scheduler",
        public_api=[
            PublicAPI(
                name="schedule_tasks",
                kind="function",
                signature="schedule_tasks(tasks: list[str], dependencies: list[tuple[str, str]]) -> list[str]",
                description="Return a valid deterministic task execution order.",
                source_sections=["1.1"],
            )
        ],
        requirements=requirements,
        constraints={
            "language": "python",
            "allowed_dependencies": ["stdlib"],
            "forbidden_side_effects": ["network", "filesystem", "process"],
        },
    )


def deterministic_code(description_text: str, module_name: str) -> str:
    if module_name != "task_scheduler" or "schedule_tasks" not in description_text:
        raise RuntimeError("No deterministic code generator for this description")
    reverse = "reverse" in description_text and "largest available" in description_text
    reverse_parameter = ", reverse=False" if reverse else ""
    reverse_branch = """
    if not isinstance(reverse, bool):
        raise TypeError("reverse must be a bool")
""" if reverse else ""
    pop_line = "heapq.heappop(available)[1] if reverse else heapq.heappop(available)" if reverse else "heapq.heappop(available)"
    push_ready = "heapq.heappush(available, (_reverse_key(downstream), downstream) if reverse else downstream)" if reverse else "heapq.heappush(available, downstream)"
    seed_ready = "heapq.heappush(available, ((-ord(task[0]) if task else 0, task) if reverse else task))" if reverse else "heapq.heappush(available, task)"
    code = f'''from __future__ import annotations

import heapq


def schedule_tasks(tasks, dependencies{reverse_parameter}):
    """Return a deterministic topological ordering for tasks."""
    if not isinstance(tasks, list):
        raise TypeError("tasks must be a list")
    if not isinstance(dependencies, list):
        raise TypeError("dependencies must be a list")
{reverse_branch}
    for task in tasks:
        if not isinstance(task, str):
            raise TypeError("task names must be strings")
    if len(set(tasks)) != len(tasks):
        raise ValueError("duplicate task names")

    task_set = set(tasks)
    graph = {{task: [] for task in tasks}}
    indegree = {{task: 0 for task in tasks}}

    for dependency in dependencies:
        if (
            not isinstance(dependency, tuple)
            and not isinstance(dependency, list)
        ) or len(dependency) != 2:
            raise TypeError("dependencies must be pairs")
        before, after = dependency
        if not isinstance(before, str) or not isinstance(after, str):
            raise TypeError("dependency tasks must be strings")
        if before not in task_set or after not in task_set:
            raise ValueError("dependency refers to unknown task")
        graph[before].append(after)
        indegree[after] += 1

    available = []
    for task in tasks:
        if indegree[task] == 0:
            {seed_ready}

    ordered = []
    while available:
        task = {pop_line}
        ordered.append(task)
        for downstream in sorted(graph[task], reverse={reverse}):
            indegree[downstream] -= 1
            if indegree[downstream] == 0:
                {push_ready}

    if len(ordered) != len(tasks):
        raise ValueError("circular dependency exists")
    return ordered
'''
    if reverse:
        code = code.replace("(-ord(task[0]) if task else 0, task)", "(_reverse_key(task), task)")
        code = code.replace("import heapq\n", "import heapq\n\n\ndef _reverse_key(value):\n    return tuple(-ord(char) for char in value)\n")
    return code


def deterministic_tests(description_text: str, module_name: str) -> str:
    if module_name != "task_scheduler" or "schedule_tasks" not in description_text:
        raise RuntimeError("No deterministic test generator for this description")
    reverse = "reverse" in description_text and "largest available" in description_text
    extra = ""
    if reverse:
        extra = '''

def test_tp_21_accepts_reverse_parameter():
    """TP_21: Accepts optional reverse parameter."""
    assert schedule_tasks(["b", "a"], [], reverse=True) == ["b", "a"]


def test_tp_22_default_reverse_false():
    """TP_22: Default reverse is False."""
    assert schedule_tasks(["b", "a"], []) == ["a", "b"]


def test_tp_23_reverse_false_smallest_first():
    """TP_23: reverse=False selects smallest available task first."""
    assert schedule_tasks(["b", "a"], [], reverse=False) == ["a", "b"]


def test_tp_24_reverse_true_largest_first():
    """TP_24: reverse=True selects largest available task first."""
    assert schedule_tasks(["a", "b", "c"], [], reverse=True) == ["c", "b", "a"]
'''
    return f'''import pytest

from {module_name} import schedule_tasks


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
{extra}
'''


def item(
    tp_id: str,
    description: str,
    source_sections: list[str],
    expected_behavior: str,
    category: str,
) -> TestPlanItem:
    match = re.search(r"(\d+)", tp_id)
    requirement_ids = [f"REQ_{int(match.group(1))}"] if match else []
    return TestPlanItem(
        tp_id,
        description,
        source_sections,
        expected_behavior,
        category,
        requirement_ids,
    )


def _item_signature(item: TestPlanItem) -> tuple[str, str, tuple[str, ...], str]:
    return (
        _normalize(item.description),
        _normalize(item.expected_behavior),
        tuple(item.source_sections),
        item.category,
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _tp_sort_key(tp_id: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", tp_id)
    return (int(match.group(1)) if match else 10**9, tp_id)
