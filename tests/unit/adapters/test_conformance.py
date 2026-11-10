"""The conformance tests every model adapter fake passes; a new family adds its fake below."""

from collections.abc import Callable

import pytest

from pyrobardfx.adapters.base import Adapter, AdapterProgress
from pyrobardfx.adapters.constants import CPU_REFUSING_FAMILIES, Backend
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.domain.constants import StageName
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.adapter import FakeAdapter
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink

type AdapterFake = Callable[[BackendOrder, FakeClock], Adapter]

# Each model adapter fake, made on a backend order with a fake clock.
ADAPTER_FAKES: tuple[AdapterFake, ...] = (FakeAdapter,)


def progress_into(sink: RecordingSink) -> AdapterProgress:
    events = FanOutBuilder.over(FakeClock(), (sink,)).at(StageName.SETTINGS)
    return AdapterProgress(events, lambda _percent: None)


def on_each_backend(make: AdapterFake) -> list[Adapter]:
    """The fake placed on each backend it may run on, one order of that backend alone each."""
    declared = make(BackendOrder(tuple(Backend)), FakeClock()).declaration
    refuses_cpu = declared.family in CPU_REFUSING_FAMILIES
    return [
        make(BackendOrder((backend,)), FakeClock())
        for backend in declared.dtypes
        if not (refuses_cpu and backend is Backend.CPU)
    ]


@pytest.mark.parametrize("make", ADAPTER_FAKES)
def test_an_adapter_fake_runs_on_at_least_one_backend(make: AdapterFake) -> None:
    assert on_each_backend(make) != []


@pytest.mark.parametrize("make", ADAPTER_FAKES)
def test_an_adapter_fake_holds_its_model_once_loaded_on_each_backend(make: AdapterFake) -> None:
    placed = on_each_backend(make)

    for adapter in placed:
        adapter.load(progress_into(RecordingSink()))

    assert all(adapter.loaded for adapter in placed)


@pytest.mark.parametrize("make", ADAPTER_FAKES)
def test_an_adapter_fake_holds_no_model_once_released_on_each_backend(make: AdapterFake) -> None:
    placed = on_each_backend(make)

    for adapter in placed:
        adapter.load(progress_into(RecordingSink()))
        adapter.release(progress_into(RecordingSink()))

    assert not any(adapter.loaded for adapter in placed)


@pytest.mark.parametrize("make", ADAPTER_FAKES)
def test_an_adapter_fake_logs_one_load_and_one_release_naming_its_backend(
    make: AdapterFake,
) -> None:
    sink = RecordingSink()
    adapter = make(BackendOrder(tuple(Backend)), FakeClock())

    adapter.load(progress_into(sink))
    adapter.release(progress_into(sink))

    assert [(e.event, e.fields["backend"]) for e in sink.events] == [
        ("model_loaded", adapter.backend),
        ("model_released", adapter.backend),
    ]
