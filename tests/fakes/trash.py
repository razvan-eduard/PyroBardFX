"""The fake trash: moves paths into a holding folder in the test's sandbox."""

from pathlib import Path

from pyrobardfx.trash.base import Trash
from tests.fakes.clock import FakeClock


class FakeTrash(Trash):
    """A trash that keeps what it is given in `holding`; it never touches the system trash.

    Each move takes `seconds_per_move` on the fake clock; a path given to `refuse` is left in place.
    """

    def __init__(self, clock: FakeClock, holding: Path, seconds_per_move: float = 0.0) -> None:
        super().__init__(clock)
        self._fake_clock = clock
        self._holding = holding
        self._seconds_per_move = seconds_per_move
        self._refused: dict[Path, OSError] = {}

    def refuse(self, path: Path, error: OSError) -> None:
        """Make every later move of `path` raise `error`, as the OS would."""
        self._refused[path] = error

    def _move(self, path: Path) -> None:
        if path in self._refused:
            raise self._refused[path]
        self._holding.mkdir(parents=True, exist_ok=True)
        path.rename(self._holding / path.name)
        self._fake_clock.advance(self._seconds_per_move)
