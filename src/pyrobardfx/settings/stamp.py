"""The settings stamp: the settings a script records, short because it holds non-defaults only.

The global settings stay out of it, so a script stays portable between working directories.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, JsonValue

from pyrobardfx.script.constants import TAGS_HEADER, VALUE_PART_SEPARATOR
from pyrobardfx.script.global_tags import GlobalTags
from pyrobardfx.script.tag_words import TagWords
from pyrobardfx.settings.constants import (
    GLOBAL_SETTINGS,
    LINE_BLANKS,
    NOT_FOUND,
    SETTINGS_KIND,
    STAMP_TAG,
    STAMP_VALUE,
)
from pyrobardfx.settings.model import Settings
from pyrobardfx.store.constants import DUMP_MODE, EXTRA_FORBID, LINE_END


class SettingsStamp(BaseModel):
    """The other settings that differ from the defaults, as JSON values by name."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    values: dict[str, JsonValue]

    @classmethod
    def of(cls, settings: Settings) -> Self:
        values = settings.model_dump(
            mode=DUMP_MODE, exclude_defaults=True, exclude=set(GLOBAL_SETTINGS)
        )
        return cls(values=values)

    def tag(self) -> str:
        """The stamp as the script writes it: one `[settings: …]` tag of name and value pairs."""
        values = VALUE_PART_SEPARATOR.join(
            STAMP_VALUE.format(name=name, value=value) for name, value in self.values.items()
        )
        return STAMP_TAG.format(kind=SETTINGS_KIND, values=values)

    def restamped(self, script: str) -> str:
        """`script` with this stamp in place of its own; every byte outside the stamp stays.

        A script with no stamp gets it on a line of its own after the tags header, or on its first
        line when it has no header.
        """
        tags = GlobalTags(TagWords.english()).read(script).tags
        span = next((tag.span for tag in tags if tag.kind == SETTINGS_KIND), None)
        if span is None:
            return self._after_header(script)
        line = script[span.start : span.end]
        # The tag's span holds its line's blanks around it; they stay as written.
        start = span.start + len(line) - len(line.lstrip(LINE_BLANKS))
        end = span.end - len(line) + len(line.rstrip(LINE_BLANKS))
        return script[:start] + self.tag() + script[end:]

    def _after_header(self, script: str) -> str:
        header = script.find(TAGS_HEADER)
        if header == NOT_FOUND:
            return self.tag() + LINE_END + script
        head, newline, rest = script[header:].partition(LINE_END)
        return script[:header] + head + LINE_END + self.tag() + newline + rest
