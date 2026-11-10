"""The fake clock: its time moves only when a test advances it."""

from datetime import UTC, datetime, timedelta

from pyrobardfx.clock.base import Clock

# The time a test's fake clock starts at unless the test names another.
START = datetime(2026, 11, 9, 15, 30, 0, tzinfo=UTC)


class FakeClock(Clock):
    """A clock that stands still until `advance` moves it; no test ever sleeps."""

    def __init__(self, start: datetime = START) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
