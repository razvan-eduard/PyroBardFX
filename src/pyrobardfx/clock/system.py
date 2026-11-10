"""The clock of the running system."""

from datetime import UTC, datetime

from pyrobardfx.clock.base import Clock


class SystemClock(Clock):
    """Reads the system time."""

    def now(self) -> datetime:
        return datetime.now(UTC)
