"""The device resolver: which backends this machine offers a model adapter, best first."""

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import Protocol

from pyrobardfx.adapters.constants import (
    ACCELERATORS,
    APPLE_SILICON_TIER,
    MLX_CORE_MODULE,
    TORCH_MODULE,
    Backend,
    DeviceChoice,
)
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError


class BackendProbe(Protocol):
    """Tells whether this machine can run models on one accelerator backend."""

    def available(self, backend: Backend) -> bool:
        """Tell whether `backend` works here; asked only for accelerators, never for the CPU."""
        ...


class SystemBackendProbe:
    """Asks the installed runtimes: torch for MPS and CUDA, MLX for Metal.

    A runtime that is not installed, or fails to import, offers no backend. The runtimes are
    imported here, by `importer`, at the first question, so the app starts without them.
    """

    def __init__(self, importer: Callable[[str], ModuleType] = importlib.import_module) -> None:
        self._import = importer

    def available(self, backend: Backend) -> bool:
        try:
            if backend is Backend.MLX:
                # A third-party module: its attributes are untyped.
                return bool(self._import(MLX_CORE_MODULE).metal.is_available())
            torch = self._import(TORCH_MODULE)
        except ImportError, OSError:
            return False
        if backend is Backend.MPS:
            return bool(torch.backends.mps.is_available())
        if backend is Backend.CUDA:
            return bool(torch.cuda.is_available())
        return False


@dataclass(frozen=True)
class BackendOrder:
    """The backends a model adapter may use, best first; the resolver's one answer per Run."""

    backends: tuple[Backend, ...]


class DeviceResolver:
    """Picks the backend order once per Run, at its start, from the probe and the Device."""

    def __init__(self, probe: BackendProbe) -> None:
        self._probe = probe

    def pick(self, flag: DeviceChoice | None, setting: DeviceChoice) -> BackendOrder:
        """Return the backends to use, best first; the CPU always closes the order.

        A given `flag`, `auto` included, wins over `setting`; with no flag the setting decides.
        `auto` gives every accelerator the probe finds, best first. A named backend goes first;
        an Apple Silicon one keeps its partner next, if the probe finds it.

        Raise `RefusedError` when the choice names an accelerator the probe does not find.
        """
        choice = setting if flag is None else flag
        if choice is DeviceChoice.AUTO:
            found = tuple(backend for backend in ACCELERATORS if self._probe.available(backend))
            return BackendOrder((*found, Backend.CPU))
        backend = Backend(choice.value)
        if backend is Backend.CPU:
            return BackendOrder((Backend.CPU,))
        if not self._probe.available(backend):
            raise RefusedError(RefusalReason.DEVICE_UNAVAILABLE, None, backend.value)
        partners = APPLE_SILICON_TIER if backend in APPLE_SILICON_TIER else ()
        found = tuple(
            partner
            for partner in partners
            if partner is not backend and self._probe.available(partner)
        )
        return BackendOrder((backend, *found, Backend.CPU))
