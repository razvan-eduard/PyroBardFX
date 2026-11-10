from pathlib import Path

from pyrobardfx.script.model import ParsedScript
from pyrobardfx.script.parser import ScriptParser
from tests.builders.script_fixtures import FIXTURES, PARSE_SUFFIX, ScriptFixtures

SCRIPT = "# The Harbour\nFog [ambience: fog, 0.4] came in.\n"


def test_writing_the_fixtures_puts_the_parse_of_each_script_beside_it(tmp_path: Path) -> None:
    (tmp_path / "harbour.txt").write_text(SCRIPT, encoding="utf-8")

    ScriptFixtures(tmp_path).write()

    written = (tmp_path / "harbour.json").read_text(encoding="utf-8")
    assert ParsedScript.model_validate_json(written) == ScriptParser.parse(SCRIPT)


def test_every_shipped_fixture_holds_the_parse_of_its_script_as_the_parser_reads_it() -> None:
    fixtures = ScriptFixtures(FIXTURES)

    assert fixtures.scripts() != []
    assert {
        script.name: script.with_suffix(PARSE_SUFFIX).read_text(encoding="utf-8")
        for script in fixtures.scripts()
    } == {script.name: fixtures.expected(script) for script in fixtures.scripts()}
