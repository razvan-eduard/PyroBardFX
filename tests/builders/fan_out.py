"""Builds the event fan-out for a test that sends events but checks no failed-sink report."""

import io
from collections.abc import Sequence

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.fan_out import EventFanOut, EventSink
from pyrobardfx.locales.constants import FALLBACK_LANGUAGE
from pyrobardfx.locales.labels import Labels


class FanOutBuilder:
    """A fan-out that reports a failed sink in en on a stream of its own, never on stderr."""

    @staticmethod
    def over(clock: Clock, sinks: Sequence[EventSink] = ()) -> EventFanOut:
        return EventFanOut(clock, sinks, io.StringIO(), Labels.load(FALLBACK_LANGUAGE))
