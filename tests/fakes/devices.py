"""The fake backend probe: says which backends the machine has, as a test names them."""

from pyrobardfx.adapters.constants import Backend


class FakeBackendProbe:
    """A backend probe that finds exactly the backends it was given; it never asks a runtime."""

    def __init__(self, *available: Backend) -> None:
        self._available = frozenset(available)
        self.asked: list[Backend] = []

    def available(self, backend: Backend) -> bool:
        """Tell whether `backend` was given; `asked` records each question, in order."""
        self.asked.append(backend)
        return backend in self._available
