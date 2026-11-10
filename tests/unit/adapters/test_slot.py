from types import MappingProxyType

from pyrobardfx.adapters.base import AdapterDeclaration, AdapterProgress
from pyrobardfx.adapters.constants import AdapterFamily, Backend, DType
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.adapters.slot import ModelSlot
from pyrobardfx.domain.constants import StageName
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.adapter import FakeAdapter
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink

CPU_ONLY = BackendOrder((Backend.CPU,))


def of_family(family: AdapterFamily) -> FakeAdapter:
    declaration = AdapterDeclaration(family, MappingProxyType({Backend.CPU: DType.FLOAT32}))
    return FakeAdapter(CPU_ONLY, FakeClock(), declaration)


def progress_into(sink: RecordingSink) -> AdapterProgress:
    events = FanOutBuilder.over(FakeClock(), (sink,)).at(StageName.SETTINGS)
    return AdapterProgress(events, lambda _percent: None)


def test_the_slot_releases_the_held_model_before_the_next_one_loads() -> None:
    sink = RecordingSink()
    slot = ModelSlot()
    slot.load(of_family(AdapterFamily.STT), progress_into(sink))

    slot.load(of_family(AdapterFamily.TTS), progress_into(sink))

    assert [(e.event, e.fields["family"]) for e in sink.events] == [
        ("model_loaded", "stt"),
        ("model_released", "stt"),
        ("model_loaded", "tts"),
    ]


def test_loading_the_held_model_again_keeps_it_loaded_without_a_release() -> None:
    sink = RecordingSink()
    slot = ModelSlot()
    adapter = of_family(AdapterFamily.STT)
    slot.load(adapter, progress_into(RecordingSink()))

    slot.load(adapter, progress_into(sink))

    assert (adapter.held, sink.events) == (True, [])


def test_emptying_the_slot_releases_the_held_model() -> None:
    sink = RecordingSink()
    slot = ModelSlot()
    adapter = of_family(AdapterFamily.STT)
    slot.load(adapter, progress_into(RecordingSink()))

    slot.empty(progress_into(sink))

    assert (adapter.held, [e.event for e in sink.events]) == (False, ["model_released"])


def test_emptying_an_empty_slot_logs_nothing() -> None:
    sink = RecordingSink()

    ModelSlot().empty(progress_into(sink))

    assert sink.events == []
