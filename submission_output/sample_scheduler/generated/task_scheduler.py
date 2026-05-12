from __future__ import annotations

import heapq


def schedule_tasks(tasks, dependencies):
    """Return a deterministic topological ordering for tasks."""
    if not isinstance(tasks, list):
        raise TypeError("tasks must be a list")
    if not isinstance(dependencies, list):
        raise TypeError("dependencies must be a list")

    for task in tasks:
        if not isinstance(task, str):
            raise TypeError("task names must be strings")
    if len(set(tasks)) != len(tasks):
        raise ValueError("duplicate task names")

    task_set = set(tasks)
    graph = {task: [] for task in tasks}
    indegree = {task: 0 for task in tasks}

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
            heapq.heappush(available, task)

    ordered = []
    while available:
        task = heapq.heappop(available)
        ordered.append(task)
        for downstream in sorted(graph[task], reverse=False):
            indegree[downstream] -= 1
            if indegree[downstream] == 0:
                heapq.heappush(available, downstream)

    if len(ordered) != len(tasks):
        raise ValueError("circular dependency exists")
    return ordered
