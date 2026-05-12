from typing import List, Tuple
import heapq


def schedule_tasks(tasks: List[str], dependencies: List[Tuple[str, str]]) -> List[str]:
    # Validate input types
    if not isinstance(tasks, list):
        raise TypeError("tasks must be a list")
    if not isinstance(dependencies, list):
        raise TypeError("dependencies must be a list")

    # Validate tasks elements
    for t in tasks:
        if not isinstance(t, str):
            raise TypeError("all tasks must be strings")

    # Validate uniqueness of tasks
    if len(set(tasks)) != len(tasks):
        raise ValueError("tasks list contains duplicates")

    task_set = set(tasks)

    # Validate dependencies elements
    for dep in dependencies:
        if not (isinstance(dep, tuple) or isinstance(dep, list)) or len(dep) != 2:
            raise TypeError("each dependency must be a pair of strings")
        before, after = dep
        if not isinstance(before, str) or not isinstance(after, str):
            raise TypeError("dependency pairs must contain strings")
        if before not in task_set or after not in task_set:
            raise ValueError("dependency references unknown task")

    # Special case: empty inputs
    if not tasks and not dependencies:
        return []

    # Build graph and in-degree count
    graph = {task: [] for task in tasks}
    in_degree = {task: 0 for task in tasks}

    for before, after in dependencies:
        graph[before].append(after)
        in_degree[after] += 1

    # Use a min-heap for lexicographically smallest available task
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

    # Check if all tasks are scheduled (detect cycle)
    if len(result) != len(tasks):
        raise ValueError("circular dependency detected")

    return result
