from pyrobardfx.script.model import ParsedScript
from pyrobardfx.script.parser import ScriptParser

GLOBALS = """[TAGS-PRESENT]
[GLOBALS-START]
[scene-all: lsd | a foggy harbour]
[ambience-all: rain, 0.3, fade long]
[fx-all: grain 0.3, vignette 0.5]
[settings: quality_preset best]
[style-look: noir | dark, grainy]
[GLOBALS-END]
The fog came in.
"""


def test_a_script_with_the_header_in_its_first_200_characters_carries_tags() -> None:
    assert ScriptParser().parse("[TAGS-PRESENT]\nThe fog came in.").tags_present is True


def test_a_header_after_the_first_200_characters_does_not_count() -> None:
    assert ScriptParser().parse("word " * 40 + "[TAGS-PRESENT]").tags_present is False


def test_the_header_and_the_globals_markers_are_not_part_of_any_paragraph() -> None:
    (chapter,) = ScriptParser().parse(GLOBALS).chapters

    assert [p.text for s in chapter.sections for p in s.paragraphs] == ["The fog came in."]


def test_each_global_tag_on_its_own_line_is_read_with_its_canonical_kind() -> None:
    script = ScriptParser().parse(GLOBALS)

    assert [(t.kind, t.value, t.volume, t.fade) for t in script.global_tags] == [
        ("visual-all", "lsd | a foggy harbour", None, None),
        ("ambience-all", "rain", 0.3, "long"),
        ("fx-all", "grain 0.3, vignette 0.5", None, None),
        ("settings", "quality_preset best", None, None),
        ("style-look", "noir | dark, grainy", None, None),
    ]


def test_the_header_and_global_tags_are_not_counted_as_spoken_words() -> None:
    (chapter,) = (
        ScriptParser().parse("[TAGS-PRESENT]\n[settings: a=b]\nShe ran [sfx: steps].").chapters
    )

    assert chapter.sections[0].paragraphs[0].tags[0].word == 2


def test_ambiance_all_is_no_global_tag_word_and_stays_text() -> None:
    script = ScriptParser().parse("[ambiance-all: rain]\nThe fog came in.")

    assert (script.global_tags, script.chapters[0].sections[0].paragraphs[0].text) == (
        (),
        "[ambiance-all: rain]\nThe fog came in.",
    )


def test_a_script_with_crlf_line_ends_parses_as_its_lf_form_but_for_offsets() -> None:
    text = GLOBALS + "\n# Two\n[video]\nRang.\n\n## Quay\nGone.\n"

    def outline(script: ParsedScript) -> list[object]:
        return [
            [(t.kind, t.value) for t in script.global_tags],
            [(c.title, c.video_break, [s.title for s in c.sections]) for c in script.chapters],
            [p.text for c in script.chapters for s in c.sections for p in s.paragraphs],
        ]

    crlf = ScriptParser().parse(text.replace("\n", "\r\n"))

    assert outline(crlf) == outline(ScriptParser().parse(text))


def test_a_global_sound_tag_keeps_its_content_id_as_an_inline_tag_does() -> None:
    (tag,) = ScriptParser().parse("[ambience-all: rain.wav #3FA2C1, 0.3]\nFog.").global_tags

    assert (tag.value, tag.content_id, tag.volume) == ("rain.wav", "3fa2c1", 0.3)
