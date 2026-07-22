from pathlib import Path

COMMANDS_DIR = Path("commands")


def get_modules() -> list[str]:
    modules = []

    for file in COMMANDS_DIR.rglob("*.py"):

        if file.name.startswith("_"):
            continue

        if file.name == "__init__.py":
            continue

        modules.append(".".join(file.with_suffix("").parts))

    return sorted(modules)