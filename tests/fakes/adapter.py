"""The fake model adapter: loads nothing, takes fake-clock time and reports its steps."""

import weakref
from types import MappingProxyType

from pyrobardfx.adapters.base import Adapter, AdapterDeclaration, AdapterProgress
from pyrobardfx.adapters.constants import AdapterFamily, Backend, DType
from pyrobardfx.adapters.devices import BackendOrder
from tests.fakes.clock import FakeClock

# The fake runs everywhere, as a transcription adapter would, with a dtype of its own per backend.
FAKE_DECLARATION = AdapterDeclaration(
    AdapterFamily.STT,
    MappingProxyType(
        {
            Backend.MLX: DType.FLOAT16,
            Backend.MPS: DType.FLOAT16,
            Backend.CUDA: DType.BFLOAT16,
            Backend.CPU: DType.FLOAT32,
        }
    ),
)


class FakeModel:
    """Stands in for a model's objects: it refers to itself, so only a collection frees it."""

    def __init__(self) -> None:
        self.itself = self


class FakeAdapter(Adapter):
    """A model adapter of `declaration`'s family whose model is a `FakeModel`, never a real one.

    A load takes `seconds_to_load` and a release `seconds_to_release` on the fake clock;
    `held` tells whether its model is in memory, as the runtime would see it. `loads` counts
    the models it brought into memory, and `freed_before_flush` tells whether the last dropped
    model was gone by the time the accelerator cache was flushed.
    """

    def __init__(
        self,
        order: BackendOrder,
        clock: FakeClock,
        declaration: AdapterDeclaration = FAKE_DECLARATION,
        seconds_to_load: float = 0.0,
        seconds_to_release: float = 0.0,
    ) -> None:
        self.declaration = declaration
        super().__init__(order, clock)
        self._fake_clock = clock
        self._seconds_to_load = seconds_to_load
        self._seconds_to_release = seconds_to_release
        self.held = False
        self.loads = 0
        self.freed_before_flush = False
        self._model: FakeModel | None = None
        self._dropped: weakref.ref[FakeModel] | None = None

    def work(self, progress: AdapterProgress, steps: int) -> None:
        """Take `steps` equal steps of work, each reported through the base's step."""
        for step in range(1, steps + 1):
            self._step(progress, 100.0 * step / steps, step=step)

    def _load(self) -> None:
        self._fake_clock.advance(self._seconds_to_load)
        self._model = FakeModel()
        self.loads += 1
        self.held = True

    def _drop(self) -> None:
        self._fake_clock.advance(self._seconds_to_release)
        if self._model is not None:
            self._dropped = weakref.ref(self._model)
        self._model = None

    def _flush(self) -> None:
        self.freed_before_flush = self._dropped is not None and self._dropped() is None
        self.held = False
