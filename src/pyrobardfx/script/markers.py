"""The marker lines of a script: the lines that open a Chapter or a Section or mark a Video."""

from dataclasses import dataclass

from pyrobardfx.script.constants import TITLE_GROUP, MarkerKind
from pyrobardfx.script.model import Span
from pyrobardfx.script.tag_words import TAG_WORDS


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
    """Tells a marker line from a line of the script's text."""

    PATTERNS = TAG_WORDS.marker_patterns()

    @classmethod
    def of(cls, line: str, start: int) -> Marker | None:
        """The marker `line` is, when it is one; `start` is the line's offset in the script."""
        stripped = line.strip()
        for kind, pattern in cls.PATTERNS:
            match = pattern.match(stripped)
            if match:
                begin = start + len(line) - len(line.lstrip())
                span = Span(start=begin, end=begin + len(stripped))
                return Marker(
                    kind=kind, title=(match.group(TITLE_GROUP) or "").strip() or None, span=span
                )
        return None

    @classmethod
    def lines(cls, text: str, said: str) -> list[ScriptLine]:
        """The lines of `said`, which is `text` with its tags blanked, each told apart."""
        lines, start = [], 0
        for line in said.splitlines(keepends=True):
            end = start + len(line)
            blank = not text[start:end].strip()
            marker = None if blank else cls.of(line, start)
            lines.append(ScriptLine(start=start, said=line, blank=blank, marker=marker))
            start = end
        return lines
