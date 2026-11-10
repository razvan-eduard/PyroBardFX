"""The size caps of `docs/CODING_STANDARDS.md` § Size, checked over every module of the package.

A function body runs from its first body statement (a docstring counts) to the function's last
line, both included; the `def` line, its decorators and its signature lines are not body lines.
A module's line count is the number of lines in its file.
"""

import ast
from pathlib import Path

SOURCE = Path(__file__).parents[2] / "src" / "pyrobardfx"
FUNCTION_BODY_CAP = 40
MODULE_CAP = 400


def modules() -> list[Path]:
    return sorted(SOURCE.rglob("*.py"))


def body_lines(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    end = function.end_lineno or function.lineno
    return end - function.body[0].lineno + 1


def test_every_function_body_is_under_the_cap() -> None:
    too_long = [
        f"{path.relative_to(SOURCE)} {node.name} (line {node.lineno}): {body_lines(node)} lines"
        for path in modules()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and body_lines(node) >= FUNCTION_BODY_CAP
    ]

    assert too_long == []


def test_every_module_is_under_the_cap() -> None:
    too_long = [
        f"{path.relative_to(SOURCE)}: {count} lines"
        for path in modules()
        if (count := len(path.read_text(encoding="utf-8").splitlines())) >= MODULE_CAP
    ]

    assert too_long == []
