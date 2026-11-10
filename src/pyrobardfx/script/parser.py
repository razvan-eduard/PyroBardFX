"""The tag parser: one script text in, one `ParsedScript` out."""

import re
from bisect import bisect_left
from collections.abc import Iterable

from pyrobardfx.script.constants import (
    BLANK,
    KIND_GROUP,
    TAGS_HEADER,
    TAGS_HEADER_REACH,
    TOKEN_PATTERN,
    UNSPOKEN_PREFIX,
    VALUE_GROUP,
)
from pyrobardfx.script.global_tags import GlobalTags
from pyrobardfx.script.markers import Markers, ScriptLine
from pyrobardfx.script.model import Chapter, ParsedScript, Span, Tag
from pyrobardfx.script.outline import OutlineBuilder
from pyrobardfx.script.tag_value import TagValue
from pyrobardfx.script.tag_words import TagWords


class ScriptParser:
    """Reads a script as the predecessor's tag grammar and the Markdown structure markers."""

    TOKEN_RE = re.compile(TOKEN_PATTERN)

    def __init__(self, words: TagWords | None = None) -> None:
        """Read tags written in `words`, the English tag words when none are given."""
        self.words = TagWords.english() if words is None else words
        self.inline_tag_re = self.words.inline_pattern()
        self.global_tags = GlobalTags(self.words)
        self.markers = Markers(self.words)

    def parse(self, text: str) -> ParsedScript:
        """Return the script's global tags and its Chapters, Sections and Paragraphs."""
        story_wide = self.global_tags.read(text)
        without_globals = self.blanked(text, story_wide.unspoken)
        matches = list(self.inline_tag_re.finditer(without_globals))
        lines = self.markers.lines(text, self.blanked(without_globals, [m.span() for m in matches]))
        spoken = self.spoken_starts(lines)
        tags = [self.tag_of(match, bisect_left(spoken, match.start())) for match in matches]
        return ParsedScript(
            tags_present=TAGS_HEADER in text[:TAGS_HEADER_REACH],
            global_tags=story_wide.tags,
            chapters=self.outline(lines, tags),
        )

    @classmethod
    def spoken_starts(cls, lines: list[ScriptLine]) -> list[int]:
        """The offset of each word a voice says: the tokens off marker lines with a letter or digit
        that are not a `#` mark."""
        return [
            line.start + token.start()
            for line in lines
            if line.marker is None
            for token in cls.TOKEN_RE.finditer(line.said)
            if any(c.isalnum() for c in token.group())
            and not token.group().startswith(UNSPOKEN_PREFIX)
        ]

    @staticmethod
    def outline(lines: list[ScriptLine], tags: list[Tag]) -> tuple[Chapter, ...]:
        """Walk the script's lines into its outline.

        A blank line ends a Paragraph; a tag goes to the Paragraph of the next line that is not a
        blank line or a marker.
        """
        builder, taken = OutlineBuilder(), 0
        starts = [tag.span.start for tag in tags]
        for line in lines:
            if line.blank:
                builder.end_paragraph()
            elif line.marker:
                builder.open(line.marker)
            else:
                last = bisect_left(starts, line.end)
                builder.add_line(BLANK.join(line.said.split()), tags[taken:last])
                taken = last
        builder.add_line("", tags[taken:])
        return builder.build()

    @staticmethod
    def blanked(text: str, spans: Iterable[tuple[int, int]]) -> str:
        """The text with each span replaced by blanks of its length."""
        for start, end in spans:
            text = text[:start] + BLANK * (end - start) + text[end:]
        return text

    def tag_of(self, match: re.Match[str], word: int) -> Tag:
        kind = self.words.kind(match.group(KIND_GROUP))
        split = TagValue.of(kind, match.group(VALUE_GROUP) or "")
        return Tag(
            kind=kind,
            value=split.value,
            volume=split.volume,
            fade=split.fade,
            content_id=split.content_id,
            word=word,
            span=Span(start=match.start(), end=match.end()),
        )
