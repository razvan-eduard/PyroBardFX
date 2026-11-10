"""The base class every model adapter family shares: backend, dtype, load, release and steps."""

import gc
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from pyrobardfx.adapters.constants import (
    BACKEND_SEPARATOR,
    CPU_REFUSING_FAMILIES,
    EVENT_MODEL_LOADED,
    EVENT_MODEL_RELEASED,
    EVENT_MODEL_STEP,
    FAMILY_LABEL_KEYS,
    AdapterFamily,
    Backend,
    DType,
)
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import PERCENT_DONE
from pyrobardfx.events.event import EventValue
from pyrobardfx.events.fan_out import StageEvents
from pyrobardfx.refusal.constants import FAMILY_FIELD, RefusalReason
from pyrobardfx.refusal.error import RefusedError


@dataclass(frozen=True)
class AdapterDeclaration:
    """What one runtime of a family declares: the backends it runs on and its dtype on each.

    The declaration keeps a read-only copy of `dtypes`, so a later change to the given dict
    changes nothing here.
    """

    family: AdapterFamily
    dtypes: Mapping[Backend, DType]

    def __post_init__(self) -> None:
        object.__setattr__(self, "dtypes", MappingProxyType(dict(self.dtypes)))


@dataclass(frozen=True)
class AdapterProgress:
    """Where an adapter reports while a stage uses it: the stage's events and its cancel check.

    `check_cancel` takes the percent reached and raises when the Run was asked to stop, as
    `Stage.check_cancel` does. `start` and `end` are the span of the Stage's percent that the
    adapter's work covers; the adapter's own progress is scaled into it.
    """

    events: StageEvents
    check_cancel: Callable[[float], None]
    start: float
    end: float

    def percent(self, done: float) -> float:
        """Return the Stage's percent once the adapter's work is `done` percent through."""
        return self.start + (self.end - self.start) * done / PERCENT_DONE


class Adapter(ABC):
    """One runtime of a model adapter family, placed on a backend once, at construction.

    Each subclass sets `declaration`; the base picks the first backend of the order it declares.
    """

    declaration: AdapterDeclaration

    def __init__(self, order: BackendOrder, clock: Clock) -> None:
        """Place the adapter on the first backend of `order` it may run on, or raise `RefusedError`.

        A family in `CPU_REFUSING_FAMILIES` may not run on the CPU, whatever its runtime declares:
        on an order of the CPU alone it is refused for the CPU, otherwise for its backends.
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

        The event is at the start of the progress's span. A loaded adapter loads nothing again and
        logs nothing. A Run asked to stop stops here, before the model comes into memory.
        """
        if self._loaded:
            return
        progress.check_cancel(progress.start)
        started = self._clock.now()
        self._load()
        self._loaded = True
        seconds = (self._clock.now() - started).total_seconds()
        progress.events.emit(
            EVENT_MODEL_LOADED,
            progress.start,
            family=self.family,
            backend=self.backend,
            dtype=self.dtype,
            seconds=seconds,
        )

    def release(self, progress: AdapterProgress) -> None:
        """Free the model's memory, collect what it left behind, and log one event with seconds.

        The event is at the start of the progress's span. An adapter that holds no model releases
        nothing and logs nothing.
        """
        if not self._loaded:
            return
        started = self._clock.now()
        self._drop()
        # The runtime frees accelerator memory only once Python has collected the model's objects.
        gc.collect()
        self._flush()
        self._loaded = False
        seconds = (self._clock.now() - started).total_seconds()
        progress.events.emit(
            EVENT_MODEL_RELEASED,
            progress.start,
            family=self.family,
            backend=self.backend,
            seconds=seconds,
        )

    def _step(self, progress: AdapterProgress, done: float, **fields: EventValue) -> None:
        """Report one step of the adapter's work, `done` percent through it, per family step.

        The event carries the Stage's percent: `done` scaled into the progress's span. A Run asked
        to stop stops here, before the step is logged.
        """
        percent = progress.percent(done)
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
        labelled = {FAMILY_FIELD: FAMILY_LABEL_KEYS[declaration.family]}
        if refuses_cpu and order.backends == (Backend.CPU,):
            raise RefusedError(
                RefusalReason.CPU_REFUSED, None, declaration.family, labelled=labelled
            )
        backends = BACKEND_SEPARATOR.join(order.backends)
        raise RefusedError(RefusalReason.BACKEND_UNSUPPORTED, None, backends, labelled=labelled)

    @abstractmethod
    def _load(self) -> None:
        """Bring the model into memory on `self.backend` with `self.dtype`."""

    @abstractmethod
    def _drop(self) -> None:
        """Drop every reference this runtime holds to the model; the base collects them next."""

    @abstractmethod
    def _flush(self) -> None:
        """Free the accelerator memory the collected model left in the runtime's cache."""
