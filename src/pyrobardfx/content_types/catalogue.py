"""The Content types a working directory offers: the shipped ones and the creator's own."""

import re
from collections.abc import Mapping
from itertools import chain
from pathlib import Path
from typing import Self

from pyrobardfx.content_types.constants import (
    ANSWER_GAP_PATTERN,
    AUTO,
    DATA_FILE_PATTERN,
    FALLBACK_CONTENT_TYPE,
    NAME_WORD_SEPARATOR,
    SHIPPED_FOLDER,
)
from pyrobardfx.content_types.detector import ContentTypeDetector
from pyrobardfx.content_types.model import ContentType
from pyrobardfx.store.constants import ENCODING
from pyrobardfx.workdir.constants import CONTENT_TYPES_FOLDER
from pyrobardfx.workdir.working_directory import WorkingDirectory


class ContentTypes:
    """Every Content type by name, read once from the data files."""

    ANSWER_GAP_RE = re.compile(ANSWER_GAP_PATTERN)

    def __init__(self, types: Mapping[str, ContentType]) -> None:
        self._types = dict(types)

    @classmethod
    def load(cls, working: WorkingDirectory, shipped: Path = SHIPPED_FOLDER) -> Self:
        """Read the shipped Content types and the creator's own from the working directory."""
        return cls({**cls._read(shipped), **cls._read(working.root / CONTENT_TYPES_FOLDER)})

    def names(self) -> tuple[str, ...]:
        """The name of each Content type, sorted."""
        return tuple(sorted(self._types))

    def get(self, name: str) -> ContentType:
        """The Content type `name`; a name none holds raises `KeyError`."""
        return self._types[name]

    def resolve(self, choice: str, script: str, detector: ContentTypeDetector) -> str:
        """The name of the Content type `choice` picks for `script`.

        `auto` asks `detector`, offering every name, and takes the name its answer holds, else
        the name whose first word it holds, else `FALLBACK_CONTENT_TYPE`. The answer may write a
        name's `_` as a space or a hyphen, in any case. Any other choice is taken as it is.
        """
        if choice != AUTO:
            return choice
        names = self.names()
        said = detector.answer(script, names).lower()
        answer = self.ANSWER_GAP_RE.sub(NAME_WORD_SEPARATOR, said)
        whole = (name for name in names if name in answer)
        first_word = (name for name in names if name.split(NAME_WORD_SEPARATOR)[0] in answer)
        return next(chain(whole, first_word), FALLBACK_CONTENT_TYPE)

    @staticmethod
    def _read(folder: Path) -> dict[str, ContentType]:
        return {
            path.stem: ContentType.model_validate_json(path.read_text(encoding=ENCODING))
            for path in folder.glob(DATA_FILE_PATTERN)
        }
