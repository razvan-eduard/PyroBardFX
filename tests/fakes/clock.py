"""The fake clock: its time moves only when a test advances it."""

from datetime import datetime, timedelta

from pyrobardfx.clock.base import Clock


class FakeClock(Clock):
    """A clock that stands still until `advance` moves it; no test ever sleeps."""

    def __init__(self, start: datetime) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
