import ast
from collections import defaultdict
from pathlib import Path

SOURCE = Path(__file__).parents[2] / "src" / "pyrobardfx"


def string_bindings() -> dict[str, set[str]]:
    """Each string a `constants.py` binds at module level, with the packages that bind it.

    Only plain string values count: ints such as `1` and `2` mean different things in different
    packages, and an enum member such as `Language.EN` refers to its one definition.
    """
    bound: defaultdict[str, set[str]] = defaultdict(set)
    for path in SOURCE.glob("*/constants.py"):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            value = node.value if isinstance(node, ast.Assign | ast.AnnAssign) else None
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                bound[value.value].add(path.parent.name)
    return bound


def test_no_string_is_bound_in_the_constants_of_two_packages() -> None:
    assert {value: areas for value, areas in string_bindings().items() if len(areas) > 1} == {}
