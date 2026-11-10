"""The device resolver: which backends this machine offers a model adapter, best first."""

import importlib
from dataclasses import dataclass
from typing import Protocol

from pyrobardfx.adapters.constants import (
    ACCELERATORS,
    MLX_CORE_MODULE,
    TORCH_MODULE,
    Backend,
    DeviceChoice,
)
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError


class DeviceProbe(Protocol):
    """Tells whether this machine can run models on one accelerator backend."""

    def available(self, backend: Backend) -> bool:
        """Tell whether `backend` works here; asked only for accelerators, never for the CPU."""
        ...


class SystemDeviceProbe:
    """Asks the installed runtimes: torch for MPS and CUDA, MLX for Metal.

    A runtime that is not installed, or fails to import, offers no backend. The runtimes are
    imported here, at the first question, so the app starts without them.
    """

    def available(self, backend: Backend) -> bool:
        try:
            if backend is Backend.MLX:
                # A third-party module: its attributes are untyped.
                return bool(importlib.import_module(MLX_CORE_MODULE).metal.is_available())
            torch = importlib.import_module(TORCH_MODULE)
        except ImportError:
            return False
        if backend is Backend.MPS:
            return bool(torch.backends.mps.is_available())
        if backend is Backend.CUDA:
            return bool(torch.cuda.is_available())
        return False


@dataclass(frozen=True)
class BackendOrder:
    """The backends a model adapter may use, best first; the resolver's one answer per start."""

    backends: tuple[Backend, ...]


class DeviceResolver:
    """Picks the backend order once at startup, from the probe and the user's device choice."""

    def __init__(self, probe: DeviceProbe) -> None:
        self._probe = probe

    def pick(self, flag: DeviceChoice, setting: DeviceChoice) -> BackendOrder:
        """Return the backends to use, best first; the CPU always closes the order.

        `flag` wins over `setting`; either one naming a backend makes it the only one before the
        CPU. With both `auto`, the order is every accelerator the probe finds, best first.

        Raise `RefusedError` when the choice names an accelerator the probe does not find.
        """
        choice = setting if flag is DeviceChoice.AUTO else flag
        if choice is DeviceChoice.AUTO:
            found = tuple(backend for backend in ACCELERATORS if self._probe.available(backend))
            return BackendOrder((*found, Backend.CPU))
        backend = Backend(choice.value)
        if backend is Backend.CPU:
            return BackendOrder((Backend.CPU,))
        if not self._probe.available(backend):
            raise RefusedError(RefusalReason.DEVICE_UNAVAILABLE, None, backend.value)
        return BackendOrder((backend, Backend.CPU))
