"""The words a script's tags are written in, one table per tag language.

English is the only tag language for now (user ruling 2026-11-10); a later tag language fills
`TAG_WORDS` with its own table. Neither the app language nor the script language picks it.
"""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from pyrobardfx.script.constants import (
    ENGLISH_GLOBAL_KIND_WORDS,
    ENGLISH_KIND_WORDS,
    ENGLISH_MARKER_WORDS,
    GLOBAL_TAG_PATTERN,
    INLINE_TAG_PATTERN,
    MARK_MARKER_PATTERNS,
    WORD_MARKER_PATTERNS,
    GlobalTagKind,
    MarkerKind,
    TagKind,
)


@dataclass(frozen=True)
class TagWords:
    """One tag language: the word of each tag kind and its other spellings, the word of each
    global tag kind, and the word of each marker tag. Words are matched in any case."""

    kinds: Mapping[str, TagKind]
    global_kinds: Mapping[str, GlobalTagKind]
    markers: Mapping[MarkerKind, str]

    def inline_pattern(self) -> re.Pattern[str]:
        """Finds an inline tag; its kind word is group `KIND_GROUP`, its text `VALUE_GROUP`."""
        return re.compile(INLINE_TAG_PATTERN.format(words=self._either(self.kinds)), re.IGNORECASE)

    def kind(self, word: str) -> TagKind:
        """The tag kind `word` names; `word` is one the inline pattern found."""
        return self.kinds[word.lower()]

    def global_pattern(self) -> re.Pattern[str]:
        """Finds a global tag standing alone on its line; its groups are an inline tag's."""
        return re.compile(
            GLOBAL_TAG_PATTERN.format(words=self._either(self.global_kinds)),
            re.IGNORECASE | re.MULTILINE,
        )

    def global_kind(self, word: str) -> GlobalTagKind:
        """The global tag kind `word` names; `word` is one the global pattern found."""
        return self.global_kinds[word.lower()]

    def marker_patterns(self) -> tuple[tuple[MarkerKind, re.Pattern[str]], ...]:
        """Each marker line's pattern, marks first, then the marker tags; group `TITLE_GROUP` is
        the title of the Chapter or Section it opens."""
        words = (
            (kind, WORD_MARKER_PATTERNS[kind].format(word=re.escape(word)))
            for kind, word in self.markers.items()
        )
        return tuple(
            (kind, re.compile(pattern, re.IGNORECASE))
            for kind, pattern in (*MARK_MARKER_PATTERNS, *words)
        )

    @staticmethod
    def _either(words: Iterable[str]) -> str:
        return "|".join(re.escape(word) for word in sorted(words, key=len, reverse=True))


ENGLISH_TAG_WORDS = TagWords(
    kinds=ENGLISH_KIND_WORDS, global_kinds=ENGLISH_GLOBAL_KIND_WORDS, markers=ENGLISH_MARKER_WORDS
)
# The tag language the parser reads.
TAG_WORDS = ENGLISH_TAG_WORDS
