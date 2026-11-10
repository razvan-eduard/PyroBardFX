"""The settings stamp: the settings a script records, short because it holds non-defaults only.

The global settings stay out of it, so a script stays portable between working directories.
"""

import json
from typing import Self

from pydantic import BaseModel, ConfigDict, JsonValue

from pyrobardfx.script.constants import TAG_CLOSE, VALUE_PART_SEPARATOR, GlobalTagKind
from pyrobardfx.script.global_tags import GlobalTags
from pyrobardfx.script.tag_words import TagWords
from pyrobardfx.settings.constants import (
    COMPACT_JSON,
    CRLF,
    GLOBAL_SETTINGS,
    LINE_BREAKS,
    STAMP_TAG,
    STAMP_VALUE,
    UNWRITABLE_VALUE_MESSAGE,
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
        """The stamp as the script writes it: one `[settings: …]` tag of name and value pairs, or
        nothing for the default settings."""
        if not self.values:
            return ""
        values = VALUE_PART_SEPARATOR.join(
            STAMP_VALUE.format(name=name, value=self._written(name, value))
            for name, value in self.values.items()
        )
        return STAMP_TAG.format(kind=GlobalTagKind.SETTINGS, values=values)

    @staticmethod
    def _written(name: str, value: JsonValue) -> str:
        """A text value as its words, any other as compact JSON: `true`, `5`, `{"a":1}`.

        A global tag ends at its first `]` and its line's end, so a value holding either, as every
        JSON list does, is refused.
        """
        text = value if isinstance(value, str) else json.dumps(value, separators=COMPACT_JSON)
        if any(character in text for character in (TAG_CLOSE, *LINE_BREAKS)):
            raise ValueError(UNWRITABLE_VALUE_MESSAGE.format(name=name, text=text))
        return text

    def restamped(self, script: str) -> str:
        """`script` with this stamp in place of its own; every byte outside the stamp stays.

        A script with no stamp gets it on a line of its own after its `[GLOBALS-START]` marker, else
        after its tags header, else on its first line; the line ends as the script's lines end. The
        default settings write no stamp: a script's own is taken out, its line left as written.
        """
        story_wide = GlobalTags(TagWords.english())
        tags = story_wide.read(script).tags
        span = next((tag.span for tag in tags if tag.kind == GlobalTagKind.SETTINGS), None)
        if span is not None:
            return script[: span.start] + self.tag() + script[span.end :]
        if not self.values:
            return script
        line_end = self._line_end(script)
        anchor = story_wide.globals_start(script) or story_wide.header(script)
        if anchor is None:
            return self.tag() + line_end + script
        line, newline, rest = script[anchor.start :].partition(LINE_END)
        if not newline:
            return script + line_end + self.tag()
        return script[: anchor.start] + line + newline + self.tag() + line_end + rest

    @staticmethod
    def _line_end(script: str) -> str:
        """The script's own line end: CRLF when its first line ends so, else LF."""
        first_line, newline, _ = script.partition(LINE_END)
        return CRLF if (first_line + newline).endswith(CRLF) else LINE_END
