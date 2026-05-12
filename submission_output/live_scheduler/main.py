from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys


MODULE_NAME = "task_scheduler"
PUBLIC_APIS = [{'name': 'schedule_tasks', 'kind': 'function', 'signature': 'schedule_tasks(tasks: list[str], dependencies: list[tuple[str, str]]) -> list[str]', 'description': 'Computes a valid execution order for tasks with dependencies, returning an ordered list of tasks such that every task appears after all of its dependencies.'}]


GENERATED_DIR = Path(__file__).resolve().parent / "generated"
if str(GENERATED_DIR) not in sys.path:
    sys.path.insert(0, str(GENERATED_DIR))


def main() -> None:
    module = import_module(MODULE_NAME)
    print(f"Generated project: task scheduler with dependencies")
    print(f"Entry module: {MODULE_NAME}")
    print("Public API:")
    for api in PUBLIC_APIS:
        name = api["name"]
        signature = api["signature"]
        description = api.get("description") or name
        available = hasattr(module, name)
        status = "available" if available else "missing"
        print(f"- {signature} [{status}]: {description}")


if __name__ == "__main__":
    main()
