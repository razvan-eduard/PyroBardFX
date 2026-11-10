"""The model slot: one model in memory at a time, so a 16 GB machine finishes a Run."""

from pyrobardfx.adapters.base import Adapter, AdapterProgress


class ModelSlot:
    """Holds at most one loaded model adapter; loading another releases the held one first."""

    def __init__(self) -> None:
        self._held: Adapter | None = None

    def load(self, adapter: Adapter, progress: AdapterProgress) -> None:
        """Release the held model, unless it is `adapter`, then load `adapter` into the slot."""
        if self._held is not None and self._held is not adapter:
            self._held.release(progress)
        self._held = adapter
        adapter.load(progress)

    def empty(self, progress: AdapterProgress) -> None:
        """Release the held model, if any, so the next stage starts with its memory free."""
        if self._held is not None:
            self._held.release(progress)
            self._held = None
