"""The base class every pipeline stage shares."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import PERCENT_DONE, PERCENT_START
from pyrobardfx.events.fan_out import EventFanOut, StageEvents
from pyrobardfx.run.cancel import CancelToken, RunCancelledError
from pyrobardfx.run.constants import (
    EVENT_RUN_CANCELLED,
    EVENT_STAGE_FINISHED,
    EVENT_STAGE_STARTED,
)
from pyrobardfx.run.snapshot import RunSnapshot


@dataclass(frozen=True)
class StageDependencies:
    """What every stage of one Run depends on: snapshot, event fan-out, clock and cancel token."""

    snapshot: RunSnapshot
    events: EventFanOut
    clock: Clock
    cancel: CancelToken


class Stage[In, Out](ABC):
    """One step of a Run: takes `In`, returns `Out`; holds snapshot, logger, clock (ADR 0002).

    Its logger is the stage's bound emitter of the Run's event fan-out.
    """

    def __init__(self, name: str, dependencies: StageDependencies) -> None:
        self.name = name
        self._dependencies = dependencies
        self._events: StageEvents = dependencies.events.at(name)

    @property
    def snapshot(self) -> RunSnapshot:
        return self._dependencies.snapshot

    @property
    def clock(self) -> Clock:
        return self._dependencies.clock

    def run(self, inputs: In) -> Out:
        """Run the stage body between its started and finished events and return its value.

        Raise `RunCancelledError` when the Run was asked to stop before the body or between steps.
        """
        self.check_cancel(PERCENT_START)
        self._events.emit(EVENT_STAGE_STARTED, PERCENT_START)
        outputs = self.body(inputs)
        self._events.emit(EVENT_STAGE_FINISHED, PERCENT_DONE)
        return outputs

    def check_cancel(self, percent: float) -> None:
        """Stop here, `percent` into the stage, if the Run was asked to stop; call between steps."""
        if self._dependencies.cancel.is_cancelled():
            self._events.emit(EVENT_RUN_CANCELLED, percent)
            raise RunCancelledError(self.name)

    @abstractmethod
    def body(self, inputs: In) -> Out:
        """Do the stage's work from the snapshot and `inputs`; return what the next stage takes."""
