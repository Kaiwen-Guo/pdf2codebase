from typing import List, Tuple
import heapq


def schedule_tasks(tasks: List[str], dependencies: List[Tuple[str, str]]) -> List[str]:
    # Validate types (REQ_10, REQ_11)
    if not isinstance(tasks, list):
        raise TypeError("tasks must be a list")
    if not isinstance(dependencies, list):
        raise TypeError("dependencies must be a list")

    # Validate tasks elements (REQ_12)
    for t in tasks:
        if not isinstance(t, str):
            raise TypeError("all task names must be strings")

    # Validate tasks uniqueness (REQ_7)
    if len(set(tasks)) != len(tasks):
        raise ValueError("tasks list contains duplicate task names")

    task_set = set(tasks)

    # Validate dependencies elements (REQ_13, REQ_8)
    for dep in dependencies:
        if (not isinstance(dep, tuple) and not isinstance(dep, list)) or len(dep) != 2:
            raise TypeError("each dependency must be a pair of strings")
        before, after = dep
        if not isinstance(before, str) or not isinstance(after, str):
            raise TypeError("dependency elements must be strings")
        if before not in task_set or after not in task_set:
            raise ValueError("dependency refers to unknown task")

    # Build graph and in-degree map
    graph = {task: [] for task in tasks}
    in_degree = {task: 0 for task in tasks}

    for before, after in dependencies:
        graph[before].append(after)
        in_degree[after] += 1

    # Use a min-heap for lexicographically smallest available task (REQ_6)
    heap = [task for task in tasks if in_degree[task] == 0]
    heapq.heapify(heap)

    result = []

    while heap:
        current = heapq.heappop(heap)
        result.append(current)
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    # Check for cycles (REQ_9)
    if len(result) != len(tasks):
        raise ValueError("circular dependency detected")

    return result
