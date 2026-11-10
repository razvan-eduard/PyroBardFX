"""The one error every refusal raises, so one printer method and one `except` serve them all."""

from pathlib import Path

from pyrobardfx.refusal.constants import REFUSED_MESSAGE, RefusalReason


class RefusedError(Exception):
    """A start or a Run was refused; `reason` keys its text, `detail` says what stood in its way."""

    def __init__(self, reason: RefusalReason, path: Path, detail: str) -> None:
        super().__init__(REFUSED_MESSAGE.format(reason=reason, path=path, detail=detail))
        self.reason = reason
        self.path = path
        self.detail = detail
