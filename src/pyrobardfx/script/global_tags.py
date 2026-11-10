"""The parts of a script that hold for the whole Story: the tags header, the
`[GLOBALS-START]` and `[GLOBALS-END]` markers, and the global tags."""

import re
from dataclasses import dataclass

from pyrobardfx.script.constants import (
    GLOBALS_MARKER_PATTERN,
    KIND_GROUP,
    SPLIT_GLOBAL_KINDS,
    TAGS_HEADER,
    VALUE_GROUP,
)
from pyrobardfx.script.model import GlobalTag, Span
from pyrobardfx.script.tag_value import TagValue
from pyrobardfx.script.tag_words import TAG_WORDS


@dataclass(frozen=True)
class StoryWide:
    """A script's global tags, and the spans of everything Story-wide that no voice says."""

    tags: tuple[GlobalTag, ...]
    unspoken: tuple[tuple[int, int], ...]


class GlobalTags:
    """Reads the global tags and finds the header and the globals markers."""

    GLOBAL_TAG_RE = TAG_WORDS.global_pattern()
    MARKER_RE = re.compile(GLOBALS_MARKER_PATTERN, re.IGNORECASE | re.MULTILINE)
    HEADER_RE = re.compile(re.escape(TAGS_HEADER))

    @classmethod
    def read(cls, text: str) -> StoryWide:
        """The global tags of `text`, and the spans of them, the header and the markers."""
        matches = list(cls.GLOBAL_TAG_RE.finditer(text))
        others = [*cls.MARKER_RE.finditer(text), *cls.HEADER_RE.finditer(text)]
        return StoryWide(
            tags=tuple(cls.tag_of(match) for match in matches),
            unspoken=tuple(match.span() for match in (*matches, *others)),
        )

    @staticmethod
    def tag_of(match: re.Match[str]) -> GlobalTag:
        kind = TAG_WORDS.global_kind(match.group(KIND_GROUP))
        text = match.group(VALUE_GROUP)
        split = TagValue.split(text) if kind in SPLIT_GLOBAL_KINDS else TagValue.whole(text)
        return GlobalTag(
            kind=kind,
            value=split.value,
            volume=split.volume,
            fade=split.fade,
            span=Span(start=match.start(), end=match.end()),
        )
