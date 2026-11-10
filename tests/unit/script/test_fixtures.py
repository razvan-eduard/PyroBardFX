from pathlib import Path

import pytest

from pyrobardfx.script.constants import GlobalTagKind
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


def test_the_fixture_writer_ends_each_line_of_a_parse_in_lf_where_the_platform_ends_it_in_crlf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_text = Path.write_text

    def windows_write_text(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        """`Path.write_text` as on Windows: with no `newline`, each `\\n` goes out as CRLF."""
        return write_text(
            path, data, encoding, errors, CRLF.decode() if newline is None else newline
        )

    monkeypatch.setattr(Path, "write_text", windows_write_text)
    (tmp_path / "harbour.txt").write_bytes(SCRIPT.encode("utf-8"))

    ScriptFixtures(tmp_path).write()

    assert CRLF not in (tmp_path / "harbour.json").read_bytes()


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


def test_the_crlf_fixture_holds_a_global_tag_of_every_kind() -> None:
    shipped = ParsedScript.model_validate_json(
        CRLF_FIXTURE.with_suffix(PARSE_SUFFIX).read_text(encoding="utf-8")
    )

    assert {tag.kind for tag in shipped.global_tags} == set(GlobalTagKind)


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
