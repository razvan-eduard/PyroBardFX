"""The parts of a script that hold for the whole Story: the tags header, the
`[GLOBALS-START]` and `[GLOBALS-END]` markers, and the global tags."""

import re
from dataclasses import dataclass

from pyrobardfx.script.constants import (
    EDGE_GROUP,
    GLOBALS_MARKER_PATTERN,
    GLOBALS_START,
    KIND_GROUP,
    TAG_CLOSE,
    TAG_OPEN,
    TAGS_HEADER,
    TAGS_HEADER_REACH,
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
        tags = list(self.global_tag_re.finditer(text))
        lines = [match.span() for match in (*tags, *self.MARKER_RE.finditer(text))]
        header = self.header(text)
        return StoryWide(
            tags=tuple(self.tag_of(match) for match in tags),
            unspoken=(*lines, *([] if header is None else [(header.start, header.end)])),
        )

    def header(self, text: str) -> Span | None:
        """Where the tags header stands; only a header in the first `TAGS_HEADER_REACH` characters
        counts, so None for a script without one."""
        match = self.HEADER_RE.search(text, 0, TAGS_HEADER_REACH)
        return None if match is None else Span(start=match.start(), end=match.end())

    def globals_start(self, text: str) -> Span | None:
        """Where the first `[GLOBALS-START]` marker's line stands, its blanks held; None for a
        script without one."""
        starts = (
            m for m in self.MARKER_RE.finditer(text) if m[EDGE_GROUP].upper() == GLOBALS_START
        )
        match = next(starts, None)
        return None if match is None else Span(start=match.start(), end=match.end())

    def tag_of(self, match: re.Match[str]) -> GlobalTag:
        """The global tag `match` found; its span is the bracket, the line's blanks around it
        left out."""
        kind = self.words.global_kind(match.group(KIND_GROUP))
        split = TagValue.of(kind, match.group(VALUE_GROUP))
        return GlobalTag(
            kind=kind,
            value=split.value,
            volume=split.volume,
            fade=split.fade,
            content_id=split.content_id,
            span=Span(
                start=match.start() + match.group().index(TAG_OPEN),
                end=match.end(VALUE_GROUP) + len(TAG_CLOSE),
            ),
        )
