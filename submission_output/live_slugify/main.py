from __future__ import annotations

from importlib import import_module


MODULE_NAME = "slugify_utility"
PUBLIC_APIS = [{'name': 'slugify', 'kind': 'function', 'signature': 'slugify(text: str) -> str', 'description': 'Converts human-readable text into a lowercase URL-safe slug string.'}]


def main() -> None:
    module = import_module(MODULE_NAME)
    print(f"Generated project: Slugify Utility")
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
