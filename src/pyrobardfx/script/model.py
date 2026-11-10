"""The parsed script: the boundary model the tag parser hands on and writes as its fixtures."""

from pydantic import BaseModel, ConfigDict

from pyrobardfx.script.constants import Fade, GlobalTagKind, TagKind
from pyrobardfx.store.constants import EXTRA_FORBID


class Span(BaseModel):
    """Where a tag or a marker stands in the script text, as character offsets, end excluded."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    start: int
    end: int


class Tag(BaseModel):
    """One inline tag: its kind, its value, its volume and fade, and the spoken words before it."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    kind: TagKind
    value: str
    volume: float | None
    fade: Fade | None
    content_id: str | None
    word: int
    span: Span


class GlobalTag(BaseModel):
    """One tag that holds for the whole Story, standing alone on its line."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    kind: GlobalTagKind
    value: str
    volume: float | None
    fade: Fade | None
    content_id: str | None
    span: Span


class Paragraph(BaseModel):
    """One blank-line block: its text with the tags taken out, and its tags in order."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    text: str
    tags: tuple[Tag, ...]


class Section(BaseModel):
    """A division of a Chapter; `marker` is None for the Section a Chapter opens with unmarked."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    title: str | None
    marker: Span | None
    paragraphs: tuple[Paragraph, ...]


class Chapter(BaseModel):
    """The largest division of a Story; `video_break` is set by a `[video]` tag."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    title: str | None
    marker: Span | None
    video_break: bool
    sections: tuple[Section, ...]


class ParsedScript(BaseModel):
    """A whole script: whether it carries the tags header, its global tags and its Chapters."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    tags_present: bool
    global_tags: tuple[GlobalTag, ...]
    chapters: tuple[Chapter, ...]
