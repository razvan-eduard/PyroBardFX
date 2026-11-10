"""Constants of the script area: the tag kinds, their spellings and the patterns of the tag grammar.

The grammar is the predecessor's (part-a §3 Grammar), extended by the kinds `visual`, `text`,
`music`, `chapter` and `video`.
"""

from enum import StrEnum


class TagKind(StrEnum):
    """The kind of an inline tag, as the parser records it whatever spelling the script used."""

    SFX = "sfx"
    AMBIENCE = "ambience"
    UNDERSCORE = "underscore"
    TRANSITION = "transition"
    MUSIC = "music"
    VISUAL = "visual"
    SUBJECT = "subject"
    FX = "fx"
    TEXT = "text"


class GlobalTagKind(StrEnum):
    """The kind of a tag that holds for the whole Story."""

    VISUAL_ALL = "visual-all"
    AMBIENCE_ALL = "ambience-all"
    FX_ALL = "fx-all"
    SETTINGS = "settings"
    STYLE_LOOK = "style-look"


class Fade(StrEnum):
    """A tag's fade word."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


# The English tag words: each tag kind's own word and the other spellings a script may use for it.
ENGLISH_KIND_WORDS = {
    **{kind.value: kind for kind in TagKind},
    "scene": TagKind.VISUAL,
}
# Joins the words of a tag language, or the fade words, into one pattern that matches any of them.
WORD_ALTERNATION = "|"
INLINE_TAG_PATTERN = r"\[\s*({words})\s*(?::\s*([^\]]*))?\]"
KIND_GROUP = 1
VALUE_GROUP = 2

# A token a voice says: it has a letter or a digit and is not a `#` mark.
TOKEN_PATTERN = r"\S+"
UNSPOKEN_PREFIX = "#"
BLANK = " "

# A sound tag's text after the colon ends in its volume and fade word, in either order, each after
# a comma: `door, 0.8, fade long`. A last part that is neither stays in the value.
VALUE_PART_SEPARATOR = ","
NUMBER_PATTERN = r"^\s*[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?\s*$"
FADE_WORD_PATTERN = r"^\s*fade\s+({words})\s*$"
FADE_GROUP = 1
VOLUME_FLOOR = 0.0
VOLUME_CAP = 2.0

# The sound kinds, inline and global: their text after the colon ends in a volume, a fade word and
# a content id. Every other kind keeps its whole text as its value.
SPLIT_VALUE_KINDS = frozenset(
    {
        TagKind.SFX,
        TagKind.AMBIENCE,
        TagKind.UNDERSCORE,
        TagKind.TRANSITION,
        TagKind.MUSIC,
        GlobalTagKind.AMBIENCE_ALL,
    }
)

# A sound's content id, written after its path in a sound tag: `door/creak.wav #3fa2c1`.
CONTENT_ID_PATTERN = r"(?:^|\s)#([0-9a-f]{6,64})\s*$"
CONTENT_ID_GROUP = 1


class MarkerKind(StrEnum):
    """What a marker line opens or marks."""

    CHAPTER = "chapter"
    SECTION = "section"
    VIDEO = "video"


# Each marker line's pattern, matched against the line with its tags blanked and its ends stripped;
# its `title` group is the title of the Chapter or Section it opens.
TITLE_GROUP = "title"
# The markers written as marks, the same in every tag language.
MARK_MARKER_PATTERNS = (
    (MarkerKind.CHAPTER, r"^#(?!#)\s*(?P<title>.*)$"),
    (MarkerKind.SECTION, r"^#{2,}\s*(?P<title>.*)$"),
    (MarkerKind.SECTION, r"^(?:-{3,}|\*{3,})(?P<title>)$"),
)
# A chapter or video tag around its word. On a line with text it breaks the line there: the text
# before ends its Paragraph and the text after starts the next (user ruling 2026-11-10).
BREAKING_MARKER_PATTERN = r"\[\s*{word}\s*(?::\s*(?P<title>[^\]]*))?\]"
BREAKING_MARKER_KINDS = (MarkerKind.CHAPTER, MarkerKind.VIDEO)
# Each marker tag's pattern around its word; a section tag needs no colon before its title, but
# its word ends at a word boundary.
WORD_MARKER_PATTERNS = {
    MarkerKind.CHAPTER: f"^{BREAKING_MARKER_PATTERN}$",
    MarkerKind.VIDEO: f"^{BREAKING_MARKER_PATTERN}$",
    MarkerKind.SECTION: r"^\[\s*{word}\b\s*:?\s*(?P<title>[^\]]*)\]$",
}
# The English word of each marker tag.
ENGLISH_MARKER_WORDS = {
    MarkerKind.CHAPTER: "chapter",
    MarkerKind.SECTION: "section",
    MarkerKind.VIDEO: "video",
}

# A script is tagged when its header stands in its first characters.
TAGS_HEADER = "[TAGS-PRESENT]"
TAGS_HEADER_REACH = 200

# The English global tag words: each global kind's own word and its other spellings.
ENGLISH_GLOBAL_KIND_WORDS = {
    **{kind.value: kind for kind in GlobalTagKind},
    "scene-all": GlobalTagKind.VISUAL_ALL,
}
# A global tag stands alone on its line; so do the globals markers. A `\r` before the line end
# stays outside the match, so a CRLF script reads as its LF form.
GLOBAL_TAG_PATTERN = r"^[ \t]*\[\s*({words})\s*:\s*([^\]]*)\][ \t]*(?=\r?$)"
GLOBALS_MARKER_PATTERN = r"^[ \t]*\[\s*GLOBALS-(?:START|END)\s*\][ \t]*(?=\r?$)"
