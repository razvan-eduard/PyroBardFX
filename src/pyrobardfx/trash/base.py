"""The base class of the trash adapter family."""

from abc import ABC, abstractmethod
from pathlib import Path

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import PERCENT_DONE
from pyrobardfx.events.fan_out import StageEvents
from pyrobardfx.trash.constants import EVENT_NOT_TRASHED, EVENT_TRASHED


class Trash(ABC):
    """Moves paths to the system trash, never deleting them outright; emits one event per path."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

    def trash(self, path: Path, events: StageEvents) -> None:
        """Move `path` to the trash and emit one event naming it and the seconds the move took.

        The event goes out through `events`, under the stage of the caller that trashes `path`.

        When the backend cannot move it, leave `path` where it is and emit one event naming it
        and the OS reason instead; a path left in place is no refusal, so nothing is raised.
        """
        started = self._clock.now()
        try:
            self._move(path)
        except OSError as error:
            reason = error.strerror or str(error)
            events.emit(EVENT_NOT_TRASHED, PERCENT_DONE, path=str(path), reason=reason)
            return
        seconds = (self._clock.now() - started).total_seconds()
        events.emit(EVENT_TRASHED, PERCENT_DONE, path=str(path), seconds=seconds)

    @abstractmethod
    def _move(self, path: Path) -> None:
        """Move `path` to this backend's trash; raise `OSError` when it cannot."""
