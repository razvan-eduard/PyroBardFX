from pathlib import Path

from pyrobardfx.script.model import ParsedScript
from pyrobardfx.script.parser import ScriptParser
from tests.builders.script_fixtures import FIXTURES, PARSE_SUFFIX, ScriptFixtures

SCRIPT = "# The Harbour\nFog [ambience: fog, 0.4] came in.\n"
CRLF_FIXTURE = FIXTURES / "crlf.txt"
CRLF = b"\r\n"
LF = b"\n"
OFFSETS = {"span", "marker"}


def test_writing_the_fixtures_puts_the_parse_of_each_script_beside_it(tmp_path: Path) -> None:
    (tmp_path / "harbour.txt").write_text(SCRIPT, encoding="utf-8")

    ScriptFixtures(tmp_path).write()

    written = (tmp_path / "harbour.json").read_text(encoding="utf-8")
    assert ParsedScript.model_validate_json(written) == ScriptParser().parse(SCRIPT)


def test_a_script_with_crlf_line_ends_is_parsed_with_its_line_ends_kept(tmp_path: Path) -> None:
    crlf = SCRIPT.replace("\n", "\r\n")
    (tmp_path / "harbour.txt").write_bytes(crlf.encode("utf-8"))
    fixtures = ScriptFixtures(tmp_path)

    (script,) = fixtures.scripts()

    assert ParsedScript.model_validate_json(fixtures.expected(script)) == ScriptParser().parse(crlf)


def test_every_shipped_fixture_holds_the_parse_of_its_script_as_the_parser_reads_it() -> None:
    fixtures = ScriptFixtures(FIXTURES)

    assert fixtures.scripts() != []
    assert {
        script.name: script.with_suffix(PARSE_SUFFIX).read_text(encoding="utf-8")
        for script in fixtures.scripts()
    } == {script.name: fixtures.expected(script) for script in fixtures.scripts()}


def test_the_crlf_fixture_ends_every_line_in_crlf_on_disk() -> None:
    lines = CRLF_FIXTURE.read_bytes().splitlines(keepends=True)

    assert lines != []
    assert [line for line in lines if not line.endswith(CRLF)] == []


def without_offsets(value: object) -> object:
    """A dump of a parse with every `span` and `marker` taken out: all that counts no characters."""
    if isinstance(value, dict):
        return {key: without_offsets(item) for key, item in value.items() if key not in OFFSETS}
    if isinstance(value, list | tuple):
        return [without_offsets(item) for item in value]
    return value


def test_the_crlf_fixture_parses_as_its_lf_form_but_for_offsets() -> None:
    shipped = ParsedScript.model_validate_json(
        CRLF_FIXTURE.with_suffix(PARSE_SUFFIX).read_text(encoding="utf-8")
    )
    lf = CRLF_FIXTURE.read_bytes().replace(CRLF, LF).decode("utf-8")

    assert without_offsets(shipped.model_dump()) == without_offsets(
        ScriptParser().parse(lf).model_dump()
    )
