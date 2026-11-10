from pyrobardfx.script.constants import KIND_GROUP, TITLE_GROUP, GlobalTagKind, MarkerKind, TagKind
from pyrobardfx.script.tag_words import TagWords

# A tag language other than English, as a later one may fill the seam.
OTHER = TagWords(
    kinds={"sunet": TagKind.SFX, "zgomot": TagKind.SFX},
    global_kinds={"scena-toata": GlobalTagKind.VISUAL_ALL},
    markers={
        MarkerKind.CHAPTER: "capitol",
        MarkerKind.SECTION: "sectiune",
        MarkerKind.VIDEO: "film",
    },
)


def test_a_tag_language_reads_its_own_kind_words_in_any_case_and_not_english_ones() -> None:
    found = OTHER.inline_pattern().findall("Door [Sunet: door] [ZGOMOT] [sfx: door]")

    assert [OTHER.kind(match[KIND_GROUP - 1]) for match in found] == [TagKind.SFX, TagKind.SFX]


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
