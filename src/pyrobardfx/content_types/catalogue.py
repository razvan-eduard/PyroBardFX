"""The Content types a working directory offers: the shipped ones and the creator's own."""

import re
from collections.abc import Mapping, Sequence
from itertools import chain
from pathlib import Path
from typing import Self

from pydantic import ValidationError

from pyrobardfx.content_types.constants import (
    ANSWER_GAP_PATTERN,
    AUTO,
    DATA_FILE_PATTERN,
    ERROR_MESSAGE_KEY,
    LOCATION_SEPARATOR,
    NAME_WORD_SEPARATOR,
    SHIPPED_FOLDER,
)
from pyrobardfx.content_types.detector import ContentTypeDetector
from pyrobardfx.content_types.model import ContentType
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.constants import ERROR_LOCATION_KEY, FIELD_SEPARATOR
from pyrobardfx.store.json_store import JsonStore
from pyrobardfx.workdir.constants import CONTENT_TYPES_FOLDER
from pyrobardfx.workdir.working_directory import WorkingDirectory


class ContentTypes:
    """Every Content type by name, read once from the data files.

    `own` is the folder of the creator's own Content types. `refused` holds a refusal for each
    data file that was skipped, naming the file.
    """

    ANSWER_GAP_RE = re.compile(ANSWER_GAP_PATTERN)

    def __init__(
        self, types: Mapping[str, ContentType], own: Path, refused: Sequence[RefusedError] = ()
    ) -> None:
        self._types = dict(types)
        self._own = own
        self.refused = tuple(refused)

    @classmethod
    def load(cls, working: WorkingDirectory, shipped: Path = SHIPPED_FOLDER) -> Self:
        """Read the shipped Content types and the creator's own from the working directory.

        An own file takes the place of the shipped one of its name. A file that is not a valid
        Content type is skipped and refused; the others still load.
        """
        own = working.root / CONTENT_TYPES_FOLDER
        types: dict[str, ContentType] = {}
        refused: list[RefusedError] = []
        listed = chain(
            JsonStore.listed(shipped, DATA_FILE_PATTERN), JsonStore.listed(own, DATA_FILE_PATTERN)
        )
        for path in listed:
            # The listing found the file, so the store never holds the blank default.
            try:
                types[path.stem] = JsonStore.open(path, ContentType.model_construct()).read()
            except (ValidationError, UnicodeDecodeError) as error:
                problem = cls._problem(error)
                refused.append(RefusedError(RefusalReason.CONTENT_TYPE_INVALID, path, problem))
        return cls(types, own, refused)

    def names(self) -> tuple[str, ...]:
        """The name of each Content type, sorted."""
        return tuple(sorted(self._types))

    def get(self, name: str) -> ContentType:
        """The Content type `name`; a name none holds raises `KeyError`."""
        return self._types[name]

    def label(self, name: str, labels: Labels) -> str:
        """The name of the Content type `name` in the language of `labels`.

        A Content type with no `label_key` is named `name`, its file's stem.
        """
        key = self.get(name).label_key
        return name if key is None else labels.label(key)

    def resolve(self, choice: str, script: str, detector: ContentTypeDetector) -> str:
        """The name of the Content type `choice` picks for `script`.

        `auto` asks `detector`, offering every name, and takes the name its answer holds, else
        the name whose first word it holds. The answer may write a name's `_` as a space or a
        hyphen, in any case. Any other choice is taken as it is. A choice no Content type holds,
        and an `auto` whose answer names none, raise `RefusedError` listing every name.
        """
        if choice != AUTO:
            if choice not in self._types:
                raise self._refusal(RefusalReason.CONTENT_TYPE_UNKNOWN)
            return choice
        names = self.names()
        said = detector.answer(script, names).lower()
        answer = self.ANSWER_GAP_RE.sub(NAME_WORD_SEPARATOR, said)
        whole = (name for name in names if name in answer)
        first_word = (name for name in names if name.split(NAME_WORD_SEPARATOR)[0] in answer)
        picked = next(chain(whole, first_word), None)
        if picked is None:
            raise self._refusal(RefusalReason.AUTO_UNRESOLVED)
        return picked

    def _refusal(self, reason: RefusalReason) -> RefusedError:
        """A refusal of the choice, pointing at the own folder and listing every name."""
        return RefusedError(reason, self._own, FIELD_SEPARATOR.join(self.names()))

    @staticmethod
    def _problem(error: ValueError) -> str:
        """What is wrong with a file: each bad field, or the parser's words where there is none."""
        if not isinstance(error, ValidationError):
            return str(error)
        return FIELD_SEPARATOR.join(
            LOCATION_SEPARATOR.join(map(str, item[ERROR_LOCATION_KEY])) or item[ERROR_MESSAGE_KEY]
            for item in error.errors()
        )
