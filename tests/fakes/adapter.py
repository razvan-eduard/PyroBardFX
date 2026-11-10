"""The fake model adapter: loads nothing, takes fake-clock time and reports its steps."""

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


class FakeAdapter(Adapter):
    """A model adapter of `declaration`'s family whose model is a flag; it never loads a model.

    A load takes `seconds_to_load` and a release `seconds_to_release` on the fake clock;
    `held` tells whether its model is in memory, as the runtime would see it.
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

    def work(self, progress: AdapterProgress, steps: int) -> None:
        """Take `steps` equal steps of work, each reported through the base's step."""
        for step in range(1, steps + 1):
            self._step(progress, 100.0 * step / steps, step=step)

    def _load(self) -> None:
        self._fake_clock.advance(self._seconds_to_load)
        self.held = True

    def _release(self) -> None:
        self._fake_clock.advance(self._seconds_to_release)
        self.held = False
