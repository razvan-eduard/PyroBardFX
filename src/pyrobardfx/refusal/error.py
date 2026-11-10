"""The one error every refusal raises, so one printer method and one `except` serve them all."""

from pathlib import Path

from pyrobardfx.refusal.constants import (
    REFUSED_MESSAGE,
    REFUSED_WITHOUT_PATH_MESSAGE,
    RefusalReason,
)


class RefusedError(Exception):
    """A start or a Run was refused; `reason` keys its text, `detail` says what stood in its way.

    `path` is the file or folder the refusal concerns; a refusal about no path, such as a device
    choice, has none.
    """

    def __init__(self, reason: RefusalReason, path: Path | None, detail: str) -> None:
        template = REFUSED_WITHOUT_PATH_MESSAGE if path is None else REFUSED_MESSAGE
        super().__init__(template.format(reason=reason, path=path, detail=detail))
        self.reason = reason
        self.path = path
        self.detail = detail
