"""The base class every model adapter family shares: backend, dtype, load, release and steps."""

import gc
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from pyrobardfx.adapters.constants import (
    BACKEND_SEPARATOR,
    CPU_REFUSING_FAMILIES,
    EVENT_MODEL_LOADED,
    EVENT_MODEL_RELEASED,
    EVENT_MODEL_STEP,
    UNSUPPORTED_DETAIL,
    AdapterFamily,
    Backend,
    DType,
)
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import PERCENT_DONE, PERCENT_START
from pyrobardfx.events.event import EventValue
from pyrobardfx.events.fan_out import StageEvents
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError


@dataclass(frozen=True)
class AdapterDeclaration:
    """What one runtime of a family declares: the backends it runs on and its dtype on each."""

    family: AdapterFamily
    dtypes: Mapping[Backend, DType]


@dataclass(frozen=True)
class AdapterProgress:
    """Where an adapter reports while a stage uses it: the stage's events and its cancel check.

    `check_cancel` takes the percent reached and raises when the Run was asked to stop, as
    `Stage.check_cancel` does.
    """

    events: StageEvents
    check_cancel: Callable[[float], None]


class Adapter(ABC):
    """One runtime of a model adapter family, placed on a backend once, at construction.

    Each subclass sets `declaration`; the base picks the first backend of the order it declares.
    """

    declaration: AdapterDeclaration

    def __init__(self, order: BackendOrder, clock: Clock) -> None:
        """Place the adapter on the first backend of `order` it may run on, or raise `RefusedError`.

        A family in `CPU_REFUSING_FAMILIES` may not run on the CPU, whatever its runtime declares.
        """
        self._clock = clock
        self.backend = self._choose(self.declaration, order)
        self.dtype = self.declaration.dtypes[self.backend]
        self._loaded = False

    @property
    def loaded(self) -> bool:
        """Tell whether the model is in memory: loaded and not released since."""
        return self._loaded

    def load(self, progress: AdapterProgress) -> None:
        """Bring the model into memory and log one event with its backend, dtype and seconds.

        A loaded adapter loads nothing again and logs nothing. A Run asked to stop stops here,
        before the model comes into memory.
        """
        if self._loaded:
            return
        progress.check_cancel(PERCENT_START)
        started = self._clock.now()
        self._load()
        self._loaded = True
        seconds = (self._clock.now() - started).total_seconds()
        progress.events.emit(
            EVENT_MODEL_LOADED,
            PERCENT_START,
            family=self.family,
            backend=self.backend,
            dtype=self.dtype,
            seconds=seconds,
        )

    def release(self, progress: AdapterProgress) -> None:
        """Free the model's memory, collect what it left behind, and log one event with seconds.

        An adapter that holds no model releases nothing and logs nothing.
        """
        if not self._loaded:
            return
        started = self._clock.now()
        self._release()
        # The runtime frees accelerator memory only once Python has dropped the model's objects.
        gc.collect()
        self._loaded = False
        seconds = (self._clock.now() - started).total_seconds()
        progress.events.emit(
            EVENT_MODEL_RELEASED,
            PERCENT_DONE,
            family=self.family,
            backend=self.backend,
            seconds=seconds,
        )

    def _step(self, progress: AdapterProgress, percent: float, **fields: EventValue) -> None:
        """Report one step of work, `percent` into it; a family's method calls it per step.

        A Run asked to stop stops here, before the step is logged.
        """
        progress.check_cancel(percent)
        progress.events.emit(EVENT_MODEL_STEP, percent, **fields)

    @property
    def family(self) -> AdapterFamily:
        return self.declaration.family

    @staticmethod
    def _choose(declaration: AdapterDeclaration, order: BackendOrder) -> Backend:
        refuses_cpu = declaration.family in CPU_REFUSING_FAMILIES
        for backend in order.backends:
            if backend in declaration.dtypes and not (refuses_cpu and backend is Backend.CPU):
                return backend
        if refuses_cpu and Backend.CPU in order.backends:
            raise RefusedError(RefusalReason.CPU_REFUSED, None, declaration.family)
        backends = BACKEND_SEPARATOR.join(order.backends)
        detail = UNSUPPORTED_DETAIL.format(family=declaration.family, backends=backends)
        raise RefusedError(RefusalReason.BACKEND_UNSUPPORTED, None, detail)

    @abstractmethod
    def _load(self) -> None:
        """Bring the model into memory on `self.backend` with `self.dtype`."""

    @abstractmethod
    def _release(self) -> None:
        """Drop every reference this runtime holds to the model and free its accelerator memory."""
