import pytest

from pyrobardfx.script.model import Chapter, Section
from pyrobardfx.script.parser import ScriptParser


def only_section(text: str) -> Section:
    (chapter,) = ScriptParser.parse(text).chapters
    (section,) = chapter.sections
    return section


def chapters_of(text: str) -> tuple[Chapter, ...]:
    return ScriptParser.parse(text).chapters


def test_blank_lines_separate_paragraphs_and_a_single_line_break_does_not() -> None:
    section = only_section("The fog came in.\nIt stayed.\n\n  \nThe bell rang.\n")

    assert [p.text for p in section.paragraphs] == [
        "The fog came in.\nIt stayed.",
        "The bell rang.",
    ]


def test_a_line_of_only_tags_stays_inside_its_paragraph() -> None:
    (paragraph,) = only_section("She knocked.\n[sfx: knock, 0.6]\nNo answer.").paragraphs

    assert (paragraph.text, [t.value for t in paragraph.tags]) == (
        "She knocked.\nNo answer.",
        ["knock"],
    )


def test_each_tag_belongs_to_the_paragraph_it_is_written_in() -> None:
    section = only_section("Rain fell [ambience: rain].\n\nThe door [sfx: door] shut.")

    assert [[t.value for t in p.tags] for p in section.paragraphs] == [["rain"], ["door"]]


def test_a_level_one_heading_opens_a_chapter_with_its_title() -> None:
    chapters = chapters_of("Before.\n\n# The Harbour\nFog.\n\n#The Bell\nRang.")

    assert [(c.title, [p.text for s in c.sections for p in s.paragraphs]) for c in chapters] == [
        (None, ["Before."]),
        ("The Harbour", ["Fog."]),
        ("The Bell", ["Rang."]),
    ]


def test_a_script_that_opens_with_a_heading_has_no_chapter_before_it() -> None:
    chapters = chapters_of("# One\nFog.")

    assert [c.title for c in chapters] == ["One"]


def test_the_words_of_a_marker_line_are_not_counted_as_spoken() -> None:
    (chapter,) = chapters_of("# The Long Night\nShe ran [sfx: steps].")

    assert chapter.sections[0].paragraphs[0].tags[0].word == 2


@pytest.mark.parametrize(
    ("marker", "title"),
    [
        ("## The Quay", "The Quay"),
        ("### Deeper", "Deeper"),
        ("---", None),
        ("-----", None),
        ("***", None),
        ("[section]", None),
        ("[section: The Quay]", "The Quay"),
        ("[Section 2]", "2"),
    ],
)
def test_a_section_marker_opens_a_section_in_the_chapter(marker: str, title: str | None) -> None:
    (chapter,) = chapters_of(f"# One\nFog.\n  {marker}  \nRang.")

    assert [(s.title, [p.text for p in s.paragraphs]) for s in chapter.sections] == [
        (None, ["Fog."]),
        (title, ["Rang."]),
    ]


@pytest.mark.parametrize("line", ["[sectiune 2]", "[sectiunea a doua]", "[partea 3]"])
def test_a_section_word_of_another_language_stays_text(line: str) -> None:
    section = only_section(f"Fog.\n\n{line}\nRang.")

    assert [p.text for p in section.paragraphs] == ["Fog.", f"{line}\nRang."]


def test_a_chapter_tag_on_its_own_line_opens_a_chapter_with_its_title() -> None:
    chapters = chapters_of("[chapter: The Harbour]\nFog.\n\n[ Chapter ]\nRang.")

    assert [(c.title, c.sections[0].paragraphs[0].text) for c in chapters] == [
        ("The Harbour", "Fog."),
        (None, "Rang."),
    ]


def test_a_video_tag_after_text_forces_a_video_break_at_the_next_chapter() -> None:
    chapters = chapters_of("# One\nFog.\n[video]\n\nMore fog.\n\n# Two\nRang.\n\n# Three\nGone.")

    assert [(c.title, c.video_break) for c in chapters] == [
        ("One", False),
        ("Two", True),
        ("Three", False),
    ]


def test_a_video_tag_right_after_a_heading_forces_a_video_break_at_that_chapter() -> None:
    chapters = chapters_of("# One\nFog.\n\n# Two\n[Video]\nRang.")

    assert [c.video_break for c in chapters] == [False, True]


def test_a_tag_in_a_heading_goes_to_the_next_paragraph_and_leaves_the_title() -> None:
    (chapter,) = chapters_of("# The Door [sfx: door]\nIt shut.")

    (paragraph,) = chapter.sections[0].paragraphs
    assert (chapter.title, [t.value for t in paragraph.tags]) == ("The Door", ["door"])


def test_a_tag_broken_over_two_lines_opens_no_chapter_and_keeps_its_content_id() -> None:
    (chapter,) = chapters_of("It shut [sfx: door/creak.wav\n#3fa2c1] hard.")

    (paragraph,) = chapter.sections[0].paragraphs
    assert (paragraph.text, paragraph.tags[0].content_id) == ("It shut hard.", "3fa2c1")


def test_a_marker_span_covers_the_marker_without_the_blanks_around_it() -> None:
    (chapter,) = chapters_of("# One\nFog.\n  ## Two  \nRang.")

    assert [(s.marker.start, s.marker.end) for s in chapter.sections if s.marker] == [(13, 19)]


def test_a_tag_span_covers_the_tag_in_the_script_text() -> None:
    (chapter,) = chapters_of("# One\nShe ran [sfx: steps].")

    span = chapter.sections[0].paragraphs[0].tags[0].span
    assert (span.start, span.end) == (14, 26)
