from pathlib import Path

from pyrobardfx.script.model import ParsedScript
from pyrobardfx.script.parser import ScriptParser
from tests.builders.script_fixtures import FIXTURES, PARSE_SUFFIX, ScriptFixtures

SCRIPT = "# The Harbour\nFog [ambience: fog, 0.4] came in.\n"
CRLF_FIXTURE = FIXTURES / "crlf.txt"
CRLF = b"\r\n"
LF = b"\n"


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

    assert fixtures.expected(script) == ScriptParser().parse(crlf).model_dump_json(indent=2) + "\n"


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


def outline(script: ParsedScript) -> list[object]:
    """Everything of a parse that does not count characters: kinds, values, titles and texts."""
    return [
        [(t.kind, t.value) for t in script.global_tags],
        [(c.title, c.video_break, [s.title for s in c.sections]) for c in script.chapters],
        [p.text for c in script.chapters for s in c.sections for p in s.paragraphs],
        [
            (t.kind, t.value)
            for c in script.chapters
            for s in c.sections
            for p in s.paragraphs
            for t in p.tags
        ],
    ]


def test_the_crlf_fixture_parses_as_its_lf_form_but_for_offsets() -> None:
    shipped = ParsedScript.model_validate_json(
        CRLF_FIXTURE.with_suffix(PARSE_SUFFIX).read_text(encoding="utf-8")
    )
    lf = CRLF_FIXTURE.read_bytes().replace(CRLF, LF).decode("utf-8")

    assert outline(shipped) == outline(ScriptParser().parse(lf))
