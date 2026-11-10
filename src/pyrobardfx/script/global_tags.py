"""The parts of a script that hold for the whole Story: the tags header, the
`[GLOBALS-START]` and `[GLOBALS-END]` markers, and the global tags."""

import re
from dataclasses import dataclass

from pyrobardfx.script.constants import (
    GLOBALS_MARKER_PATTERN,
    KIND_GROUP,
    TAGS_HEADER,
    VALUE_GROUP,
)
from pyrobardfx.script.model import GlobalTag, Span
from pyrobardfx.script.tag_value import TagValue
from pyrobardfx.script.tag_words import TagWords


@dataclass(frozen=True)
class StoryWide:
    """A script's global tags, and the spans of everything Story-wide that no voice says."""

    tags: tuple[GlobalTag, ...]
    unspoken: tuple[tuple[int, int], ...]


class GlobalTags:
    """Reads the global tags and finds the header and the globals markers."""

    MARKER_RE = re.compile(GLOBALS_MARKER_PATTERN, re.IGNORECASE | re.MULTILINE)
    HEADER_RE = re.compile(re.escape(TAGS_HEADER))

    def __init__(self, words: TagWords) -> None:
        self.words = words
        self.global_tag_re = words.global_pattern()

    def read(self, text: str) -> StoryWide:
        """The global tags of `text`, and the spans of them, the header and the markers."""
        matches = list(self.global_tag_re.finditer(text))
        others = [*self.MARKER_RE.finditer(text), *self.HEADER_RE.finditer(text)]
        return StoryWide(
            tags=tuple(self.tag_of(match) for match in matches),
            unspoken=tuple(match.span() for match in (*matches, *others)),
        )

    def tag_of(self, match: re.Match[str]) -> GlobalTag:
        kind = self.words.global_kind(match.group(KIND_GROUP))
        split = TagValue.of(kind, match.group(VALUE_GROUP))
        return GlobalTag(
            kind=kind,
            value=split.value,
            volume=split.volume,
            fade=split.fade,
            content_id=split.content_id,
            span=Span(start=match.start(), end=match.end()),
        )
