"""The outline of a script as its lines are read: Chapters holding Sections holding Paragraphs."""

from dataclasses import dataclass, field

from pyrobardfx.script.constants import MarkerKind
from pyrobardfx.script.markers import Marker
from pyrobardfx.script.model import Chapter, Paragraph, Section, Span, Tag
from pyrobardfx.store.constants import LINE_END


@dataclass
class ParagraphDraft:
    """The lines and tags of the Paragraph being read."""

    lines: list[str] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)

    def build(self) -> Paragraph:
        return Paragraph(text=LINE_END.join(self.lines), tags=tuple(self.tags))


@dataclass
class SectionDraft:
    """A Section being read; one with no marker is the Section a Chapter opens with."""

    title: str | None = None
    marker: Span | None = None
    paragraphs: list[Paragraph] = field(default_factory=list)

    def kept(self) -> bool:
        """Whether the Section stays in the outline: it has a marker or holds a Paragraph."""
        return self.marker is not None or bool(self.paragraphs)

    def build(self) -> Section:
        return Section(title=self.title, marker=self.marker, paragraphs=tuple(self.paragraphs))


@dataclass
class ChapterDraft:
    """A Chapter being read; one with no marker holds what stands before the first heading."""

    title: str | None = None
    marker: Span | None = None
    video_break: bool = False
    sections: list[SectionDraft] = field(default_factory=lambda: [SectionDraft()])

    def holds_paragraph(self) -> bool:
        """Whether a Section of the Chapter holds a Paragraph."""
        return any(section.paragraphs for section in self.sections)

    def kept(self) -> bool:
        """Whether the Chapter stays in the outline: it has a marker or holds a Section."""
        return self.marker is not None or any(section.kept() for section in self.sections)

    def build(self) -> Chapter:
        return Chapter(
            title=self.title,
            marker=self.marker,
            video_break=self.video_break,
            sections=tuple(section.build() for section in self.sections if section.kept()),
        )


class OutlineBuilder:
    """Collects the script's lines into Chapters, Sections and Paragraphs, in reading order."""

    def __init__(self) -> None:
        self.chapters = [ChapterDraft()]
        self.paragraph = ParagraphDraft()
        self.video_break_ahead = False

    def open(self, marker: Marker) -> None:
        """Close the Paragraph being read and open what `marker` opens."""
        self.end_paragraph()
        if marker.kind is MarkerKind.CHAPTER:
            chapter = ChapterDraft(marker.title, marker.span, video_break=self.video_break_ahead)
            self.chapters.append(chapter)
            self.video_break_ahead = False
        elif marker.kind is MarkerKind.VIDEO:
            self.mark_video()
        else:
            section = SectionDraft(title=marker.title, marker=marker.span)
            self.chapters[-1].sections.append(section)

    def mark_video(self) -> None:
        """Force a Video break at the Chapter just opened, while it holds no Paragraph yet, else
        at the next Chapter."""
        chapter = self.chapters[-1]
        if chapter.marker is not None and not chapter.holds_paragraph():
            chapter.video_break = True
        else:
            self.video_break_ahead = True

    def add_line(self, text: str, tags: list[Tag]) -> None:
        """Add one line of the Paragraph being read; `text` is empty for a line of only tags."""
        if text:
            self.paragraph.lines.append(text)
        self.paragraph.tags.extend(tags)

    def end_paragraph(self) -> None:
        """Close the Paragraph being read, keeping it when it holds text or tags."""
        if self.paragraph.lines or self.paragraph.tags:
            self.chapters[-1].sections[-1].paragraphs.append(self.paragraph.build())
        self.paragraph = ParagraphDraft()

    def build(self) -> tuple[Chapter, ...]:
        self.end_paragraph()
        return tuple(chapter.build() for chapter in self.chapters if chapter.kept())
