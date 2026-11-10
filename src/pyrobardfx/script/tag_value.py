"""The parts of a tag's text after the colon: its value, volume and fade word."""

import re
from dataclasses import dataclass

from pyrobardfx.script.constants import (
    CONTENT_ID_GROUP,
    CONTENT_ID_PATTERN,
    FADE_GROUP,
    FADE_WORD_PATTERN,
    NUMBER_PATTERN,
    VALUE_PART_SEPARATOR,
    VOLUME_CAP,
    VOLUME_FLOOR,
    Fade,
)


@dataclass(frozen=True)
class SplitValue:
    """A tag's value with its volume, fade word and content id taken off its end."""

    value: str
    volume: float | None
    fade: Fade | None
    content_id: str | None = None


class TagValue:
    """Splits a sound tag's text as the predecessor did: `door.wav #3fa2c1, 0.8, fade long`."""

    NUMBER_RE = re.compile(NUMBER_PATTERN)
    CONTENT_ID_RE = re.compile(CONTENT_ID_PATTERN, re.IGNORECASE)
    FADE_WORD_RE = re.compile(FADE_WORD_PATTERN.format(words="|".join(Fade)), re.IGNORECASE)

    @staticmethod
    def whole(text: str) -> SplitValue:
        """Keep all of `text` as the value."""
        return SplitValue(value=text.strip(), volume=None, fade=None)

    @classmethod
    def split(cls, text: str) -> SplitValue:
        """Take the volume and the fade word off the end of `text`, in either order."""
        value, volume, fade = text.strip(), None, None
        while VALUE_PART_SEPARATOR in value:
            head, _, last = value.rpartition(VALUE_PART_SEPARATOR)
            fade_word = cls.FADE_WORD_RE.match(last)
            if fade_word and fade is None:
                fade = Fade(fade_word.group(FADE_GROUP).lower())
            elif volume is None and cls.NUMBER_RE.match(last):
                volume = min(VOLUME_CAP, max(VOLUME_FLOOR, float(last)))
            else:
                break
            value = head.strip()
        content_id = cls.CONTENT_ID_RE.search(value)
        if content_id is None:
            return SplitValue(value=value, volume=volume, fade=fade)
        return SplitValue(
            value=value[: content_id.start()].strip(),
            volume=volume,
            fade=fade,
            content_id=content_id.group(CONTENT_ID_GROUP).lower(),
        )
