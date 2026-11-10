"""The cancel token: the seam through which a job asks a running Run to stop."""

import threading
from typing import Protocol

from pyrobardfx.domain.constants import StageName


class CancelToken(Protocol):
    """Tells a Run whether it was asked to stop; the job manager holds the other end."""

    def is_cancelled(self) -> bool:
        """Tell whether the Run was asked to stop."""
        ...


class RunCancelledError(Exception):
    """The Run was asked to stop; the stage named `stage` stopped at a cancel check."""

    def __init__(self, stage: StageName) -> None:
        super().__init__(stage)
        self.stage = stage


class ThreadCancelToken:
    """The cancel token of a running app: set once by `cancel()`, from any thread."""

    def __init__(self) -> None:
        self._set = threading.Event()

    def cancel(self) -> None:
        """Ask the Run to stop at its next cancel check."""
        self._set.set()

    def is_cancelled(self) -> bool:
        return self._set.is_set()
