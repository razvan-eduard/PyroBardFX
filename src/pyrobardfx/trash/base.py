"""The base class of the trash adapter family."""

from abc import ABC, abstractmethod
from pathlib import Path

import structlog
from structlog.typing import FilteringBoundLogger

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import PERCENT_DONE
from pyrobardfx.trash.constants import EVENT_NOT_TRASHED, EVENT_TRASHED, LOGGER_NAME, STAGE_NAME


class Trash(ABC):
    """Moves paths to the system trash, never deleting them outright; logs one event per path."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._log: FilteringBoundLogger = structlog.get_logger(LOGGER_NAME)

    def trash(self, path: Path) -> None:
        """Move `path` to the trash and log one event naming it and the seconds the move took.

        When the backend cannot move it, leave `path` where it is and log one event naming it
        and the OS reason instead; a path left in place is no refusal, so nothing is raised.
        """
        started = self._clock.now()
        try:
            self._move(path)
        except OSError as error:
            reason = error.strerror or str(error)
            self._log.warning(
                EVENT_NOT_TRASHED,
                stage=STAGE_NAME,
                percent=PERCENT_DONE,
                path=str(path),
                reason=reason,
            )
            return
        seconds = (self._clock.now() - started).total_seconds()
        self._log.info(
            EVENT_TRASHED, stage=STAGE_NAME, percent=PERCENT_DONE, path=str(path), seconds=seconds
        )

    @abstractmethod
    def _move(self, path: Path) -> None:
        """Move `path` to this backend's trash; raise `OSError` when it cannot."""
