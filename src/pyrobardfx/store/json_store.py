"""One hand-readable JSON file behind a pydantic model, replaced whole on every write."""

import json
import os
import secrets
from pathlib import Path
from typing import Self

from pydantic import BaseModel

from pyrobardfx.store.constants import (
    DUMP_MODE,
    ENCODING,
    JSON_INDENT,
    LINE_END,
    TEMP_NAME,
    TEMP_TOKEN_BYTES,
    WRITE_MODE,
)


class JsonStore[M: BaseModel]:
    """The one writer of one JSON file; reads are served from the in-memory copy."""

    def __init__(self, path: Path, value: M) -> None:
        self._path = path
        self._value = value.model_copy(deep=True)

    @classmethod
    def open(cls, path: Path, default: M) -> Self:
        """Load the file at `path` as the model of `default`, or hold `default` when there is none.

        Opening never writes; the file appears with the first `write`.
        """
        if not path.exists():
            return cls(path, default)
        return cls(path, type(default).model_validate_json(path.read_text(encoding=ENCODING)))

    def read(self) -> M:
        """Return a copy of the in-memory value; changing it never changes the store."""
        return self._value.model_copy(deep=True)

    def write(self, value: M) -> None:
        """Replace the file whole: a write cut short leaves the old file or no file, never half."""
        text = json.dumps(value.model_dump(mode=DUMP_MODE), indent=JSON_INDENT, ensure_ascii=False)
        token = secrets.token_hex(TEMP_TOKEN_BYTES)
        temp = self._path.with_name(TEMP_NAME.format(name=self._path.name, token=token))
        try:
            with temp.open(WRITE_MODE, encoding=ENCODING) as handle:
                handle.write(text + LINE_END)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self._path)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
        self._value = value.model_copy(deep=True)
