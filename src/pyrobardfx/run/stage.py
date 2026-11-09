"""The base class every pipeline stage shares."""

from abc import ABC, abstractmethod

from structlog.typing import FilteringBoundLogger

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import PERCENT_DONE, PERCENT_START
from pyrobardfx.run.constants import EVENT_STAGE_FINISHED, EVENT_STAGE_STARTED
from pyrobardfx.run.snapshot import RunSnapshot


class Stage(ABC):
    """One step of a Run; holds the run snapshot, the Run's logger and the clock (ADR 0002)."""

    def __init__(
        self, name: str, snapshot: RunSnapshot, log: FilteringBoundLogger, clock: Clock
    ) -> None:
        self.name = name
        self._snapshot = snapshot
        self._log = log
        self._clock = clock

    @property
    def snapshot(self) -> RunSnapshot:
        return self._snapshot

    @property
    def clock(self) -> Clock:
        return self._clock

    def run(self) -> None:
        """Run the stage body between its started and finished events."""
        self._log.info(EVENT_STAGE_STARTED, stage=self.name, percent=PERCENT_START)
        self.body()
        self._log.info(EVENT_STAGE_FINISHED, stage=self.name, percent=PERCENT_DONE)

    @abstractmethod
    def body(self) -> None:
        """Do the stage's work from the snapshot and its inputs."""
