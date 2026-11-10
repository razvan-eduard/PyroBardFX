"""The base class of the clock adapter family."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime


class Clock(ABC):
    """Tells the time; the one place a timestamp comes from."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current time with its zone attached."""

    def utc_now(self) -> datetime:
        """Return the current time in UTC, whatever zone the runtime reports it in."""
        return self.now().astimezone(UTC)
