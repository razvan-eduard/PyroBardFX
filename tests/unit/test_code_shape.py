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
DEF_LINE = "def f() -> None:\n"
DOCSTRING_LINE = '    """Doc."""\n'
STATEMENT_LINE = "    x = 1\n"


def modules() -> list[Path]:
    return sorted(SOURCE.rglob("*.py"))


def body_lines(function: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    end = function.end_lineno or function.lineno
    return end - function.body[0].lineno + 1


def over_cap(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return body_lines(function) >= FUNCTION_BODY_CAP


def test_every_function_body_is_under_the_cap() -> None:
    too_long = [
        f"{path.relative_to(SOURCE)} {node.name} (line {node.lineno}): {body_lines(node)} lines"
        for path in modules()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and over_cap(node)
    ]

    assert too_long == []


def test_every_module_is_under_the_cap() -> None:
    too_long = [
        f"{path.relative_to(SOURCE)}: {count} lines"
        for path in modules()
        if (count := len(path.read_text(encoding="utf-8").splitlines())) >= MODULE_CAP
    ]

    assert too_long == []


def parsed(source: str) -> ast.FunctionDef:
    """The one function of `source`."""
    function = ast.parse(source).body[0]
    assert isinstance(function, ast.FunctionDef)
    return function


def inline_function(body: int) -> ast.FunctionDef:
    """A function of `body` body lines: a docstring and `body - 1` statements."""
    return parsed(DEF_LINE + DOCSTRING_LINE + STATEMENT_LINE * (body - 1))


def test_a_body_counts_its_docstring_but_not_its_decorator_or_signature_lines() -> None:
    function = parsed("@decorator\ndef f(\n    a: int,\n) -> None:\n" + DOCSTRING_LINE)

    assert body_lines(function) == 1


def test_a_39_line_body_is_under_the_cap_and_a_40_line_body_is_not() -> None:
    assert (over_cap(inline_function(39)), over_cap(inline_function(40))) == (False, True)
