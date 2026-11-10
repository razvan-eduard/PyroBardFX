from pyrobardfx.script.constants import KIND_GROUP, TITLE_GROUP, GlobalTagKind, MarkerKind, TagKind
from pyrobardfx.script.parser import ScriptParser
from pyrobardfx.script.tag_words import TagWords

# A tag language other than English, as a later one may fill the seam.
OTHER = TagWords(
    kinds={"sunet": TagKind.ONE_SHOT, "zgomot": TagKind.ONE_SHOT},
    global_kinds={"scena-toata": GlobalTagKind.VISUAL_ALL},
    markers={
        MarkerKind.CHAPTER: "capitol",
        MarkerKind.SECTION: "sectiune",
        MarkerKind.VIDEO: "film",
    },
)


def test_a_tag_language_reads_its_own_kind_words_in_any_case_and_not_english_ones() -> None:
    found = OTHER.inline_pattern().findall("Door [Sunet: door] [ZGOMOT] [sfx: door]")

    assert [OTHER.kind(match[KIND_GROUP - 1]) for match in found] == [
        TagKind.ONE_SHOT,
        TagKind.ONE_SHOT,
    ]


def test_a_tag_language_reads_its_own_global_kind_words_and_not_english_ones() -> None:
    found = OTHER.global_pattern().findall("[Scena-Toata: a harbour]\n[visual-all: a quay]")

    assert [OTHER.global_kind(match[KIND_GROUP - 1]) for match in found] == [
        GlobalTagKind.VISUAL_ALL
    ]


def marker_of(words: TagWords, line: str) -> tuple[MarkerKind, str | None] | None:
    for kind, pattern in words.marker_patterns():
        if match := pattern.match(line):
            return kind, match.group(TITLE_GROUP) or None
    return None


def test_a_tag_language_reads_its_own_marker_words_and_not_english_ones() -> None:
    lines = ["[Capitol: The Harbour]", "[sectiune 2]", "[film]", "[chapter]", "[section]", "# One"]

    assert [marker_of(OTHER, line) for line in lines] == [
        (MarkerKind.CHAPTER, "The Harbour"),
        (MarkerKind.SECTION, "2"),
        (MarkerKind.VIDEO, None),
        None,
        None,
        (MarkerKind.CHAPTER, "One"),
    ]


def test_the_parser_reads_the_tag_language_it_is_given_and_english_by_default() -> None:
    text = "[Capitol: The Harbour]\nDoor [sunet: door] [sfx: steps]."

    other, english = ScriptParser(OTHER).parse(text), ScriptParser().parse(text)

    assert [(c.title, c.sections[0].paragraphs[0].text) for c in other.chapters] == [
        ("The Harbour", "Door [sfx: steps].")
    ]
    assert [t.value for t in english.chapters[0].sections[0].paragraphs[0].tags] == ["steps"]
