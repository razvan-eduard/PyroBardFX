"""The marker lines of a script: the lines that open a Chapter or a Section or mark a Video."""

import re
from dataclasses import dataclass

from pyrobardfx.script.constants import TITLE_GROUP, MarkerKind
from pyrobardfx.script.model import Span
from pyrobardfx.script.tag_words import TagWords


@dataclass(frozen=True)
class Marker:
    """One marker line: what it opens, the title it gives, and where it stands."""

    kind: MarkerKind
    title: str | None
    span: Span


@dataclass(frozen=True)
class ScriptLine:
    """One line of the script with its tags blanked: where it starts, and what kind of line it is.

    `blank` holds for a line with nothing on it in the script itself, so a line of only tags is
    not blank.
    """

    start: int
    said: str
    blank: bool
    marker: Marker | None

    @property
    def end(self) -> int:
        return self.start + len(self.said)


class Markers:
    """Tells a marker line from a line of the script's text, and breaks a line of text at each
    chapter or video tag it holds."""

    def __init__(self, words: TagWords) -> None:
        self.patterns = words.marker_patterns()
        self.breaking = words.breaking_patterns()

    def of(self, line: str, start: int) -> Marker | None:
        """The marker `line` is, when it is one; `start` is the line's offset in the script."""
        stripped = line.strip()
        for kind, pattern in self.patterns:
            match = pattern.match(stripped)
            if match:
                return self.marker(kind, match, start + len(line) - len(line.lstrip()))
        return None

    def lines(self, text: str, said: str) -> list[ScriptLine]:
        """The lines of `said`, which is `text` with its tags blanked, each told apart; a line
        with text and a chapter or video tag is broken into its pieces there."""
        lines, start = [], 0
        for line in said.splitlines(keepends=True):
            marker = None if self.blank(text, start, line) else self.of(line, start)
            if marker is None:
                lines.extend(self.pieces(text, line, start))
            else:
                lines.append(ScriptLine(start=start, said=line, blank=False, marker=marker))
            start += len(line)
        return lines

    def pieces(self, text: str, line: str, start: int) -> list[ScriptLine]:
        """`line`, which is no marker line, broken at each chapter or video tag it holds."""
        found = sorted(
            ((match, kind) for kind, pattern in self.breaking for match in pattern.finditer(line)),
            key=lambda pair: pair[0].start(),
        )
        pieces, cursor = [], 0
        for match, kind in found:
            if match.start() < cursor:
                continue
            pieces.append(self.text_line(text, line[cursor : match.start()], start + cursor))
            marker = self.marker(kind, match, start + match.start())
            pieces.append(
                ScriptLine(start=marker.span.start, said=match.group(), blank=False, marker=marker)
            )
            cursor = match.end()
        pieces.append(self.text_line(text, line[cursor:], start + cursor))
        return [piece for piece in pieces if piece.said]

    @classmethod
    def text_line(cls, text: str, said: str, start: int) -> ScriptLine:
        return ScriptLine(start=start, said=said, blank=cls.blank(text, start, said), marker=None)

    @staticmethod
    def blank(text: str, start: int, said: str) -> bool:
        """Whether the script itself has nothing where `said` stands."""
        return not text[start : start + len(said)].strip()

    @staticmethod
    def marker(kind: MarkerKind, match: re.Match[str], begin: int) -> Marker:
        """The marker `match` found at offset `begin` of the script."""
        title = (match.group(TITLE_GROUP) or "").strip() or None
        return Marker(
            kind=kind, title=title, span=Span(start=begin, end=begin + len(match.group()))
        )
