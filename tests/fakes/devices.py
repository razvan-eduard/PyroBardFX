"""The fake device probe: says which backends the machine has, as a test names them."""

from pyrobardfx.adapters.constants import Backend


class FakeDeviceProbe:
    """A device probe that finds exactly the backends it was given; it never touches hardware."""

    def __init__(self, *available: Backend) -> None:
        self._available = frozenset(available)

    def available(self, backend: Backend) -> bool:
        return backend in self._available
