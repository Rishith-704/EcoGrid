import ast
from pathlib import Path

import pytest

ECOGRID_DIR = Path(__file__).resolve().parents[2] / "ecogrid"
CONTEXTS = ["marketplace", "meter_ingestion", "settlement"]


def imported_modules(file_path: Path) -> list[str]:
    """Return every module name imported by a Python file."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def find_violations(package: str, forbidden: list[str]) -> list[str]:
    """List files in a package that import any of the forbidden contexts."""
    violations = []
    for file_path in (ECOGRID_DIR / package).glob("*.py"):
        for module in imported_modules(file_path):
            for name in forbidden:
                if module == f"ecogrid.{name}" or module.startswith(f"ecogrid.{name}."):
                    violations.append(f"{file_path.name} imports {module}")
    return violations


@pytest.mark.parametrize("context", CONTEXTS)
def test_context_does_not_import_other_contexts(context):
    others = [name for name in CONTEXTS if name != context]

    violations = find_violations(context, others)

    assert violations == [], f"{context} has forbidden imports: {violations}"


def test_shared_does_not_import_any_context():
    violations = find_violations("shared", CONTEXTS)

    assert violations == [], f"shared has forbidden imports: {violations}"