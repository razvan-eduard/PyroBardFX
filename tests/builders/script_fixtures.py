"""Writes the tag parser's fixtures: beside each script `<name>.txt`, its parse as `<name>.json`.

The editor's grammar parses the same scripts and is checked against these files (story 27).
Refresh them after a grammar change with `uv run python -m tests.builders.script_fixtures`.
"""

from pathlib import Path

from pyrobardfx.script.parser import ScriptParser

FIXTURES = Path(__file__).parents[1] / "fixtures" / "script"
SCRIPT_SUFFIX = ".txt"
PARSE_SUFFIX = ".json"
ENCODING = "utf-8"
INDENT = 2


class ScriptFixtures:
    """The fixture scripts of one folder and the parse the parser writes for each."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder

    def scripts(self) -> list[Path]:
        return sorted(self._folder.glob(f"*{SCRIPT_SUFFIX}"))

    def expected(self, script: Path) -> str:
        """The parse of `script` as its fixture file holds it."""
        parsed = ScriptParser.parse(script.read_text(encoding=ENCODING))
        return parsed.model_dump_json(indent=INDENT) + "\n"

    def write(self) -> list[Path]:
        """Write the parse of every script; return the files written."""
        written = []
        for script in self.scripts():
            target = script.with_suffix(PARSE_SUFFIX)
            target.write_text(self.expected(script), encoding=ENCODING)
            written.append(target)
        return written


if __name__ == "__main__":
    ScriptFixtures(FIXTURES).write()
