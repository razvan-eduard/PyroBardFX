"""Builds the progress a stage hands a model adapter, over fakes, with its events in one sink."""

from typing import Self

from pyrobardfx.adapters.base import AdapterProgress
from pyrobardfx.domain.constants import StageName
from pyrobardfx.events.constants import PERCENT_DONE, PERCENT_START
from pyrobardfx.run.cancel import RunCancelledError
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink


class AdapterProgressBuilder:
    """Fluent builder of the progress of a stage whose events go to `sink`.

    By default the Run is never asked to stop and the adapter's work spans the whole stage.
    """

    def __init__(self, sink: RecordingSink) -> None:
        self._sink = sink
        self._cancel = FakeCancelToken()
        self._start = PERCENT_START
        self._end = PERCENT_DONE

    def span(self, start: float, end: float) -> Self:
        """Give the adapter's work the stage's percent from `start` to `end`."""
        self._start = start
        self._end = end
        return self

    def cancel(self, cancel: FakeCancelToken) -> Self:
        """Ask `cancel` at each cancel check; a cancelled one raises the stage's cancel error."""
        self._cancel = cancel
        return self

    def build(self) -> AdapterProgress:
        token = self._cancel

        def check_cancel(percent: float) -> None:
            if token.is_cancelled():
                raise RunCancelledError(StageName.SETTINGS)

        events = FanOutBuilder.over(FakeClock(), (self._sink,)).at(StageName.SETTINGS)
        return AdapterProgress(events, check_cancel, self._start, self._end)
