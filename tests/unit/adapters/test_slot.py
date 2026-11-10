from types import MappingProxyType

from pyrobardfx.adapters.base import AdapterDeclaration
from pyrobardfx.adapters.constants import AdapterFamily, Backend, DType
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.adapters.slot import ModelSlot
from tests.builders.adapter_progress import AdapterProgressBuilder
from tests.fakes.adapter import FakeAdapter
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink

CPU_ONLY = BackendOrder((Backend.CPU,))


def of_family(family: AdapterFamily) -> FakeAdapter:
    declaration = AdapterDeclaration(family, MappingProxyType({Backend.CPU: DType.FLOAT32}))
    return FakeAdapter(CPU_ONLY, FakeClock(), declaration)


def test_the_slot_releases_the_held_model_before_the_next_one_loads() -> None:
    sink = RecordingSink()
    slot = ModelSlot()
    slot.load(of_family(AdapterFamily.STT), AdapterProgressBuilder(sink).build())

    slot.load(of_family(AdapterFamily.TTS), AdapterProgressBuilder(sink).build())

    assert [(e.event, e.fields["family"]) for e in sink.events] == [
        ("model_loaded", "stt"),
        ("model_released", "stt"),
        ("model_loaded", "tts"),
    ]


def test_the_next_stage_logs_the_release_and_the_load_at_the_start_of_its_span() -> None:
    sink = RecordingSink()
    slot = ModelSlot()
    slot.load(of_family(AdapterFamily.STT), AdapterProgressBuilder(RecordingSink()).build())

    slot.load(of_family(AdapterFamily.TTS), AdapterProgressBuilder(sink).span(10.0, 90.0).build())

    assert [(e.event, e.percent) for e in sink.events] == [
        ("model_released", 10.0),
        ("model_loaded", 10.0),
    ]


def test_loading_the_held_model_again_keeps_it_loaded_without_a_release() -> None:
    sink = RecordingSink()
    slot = ModelSlot()
    adapter = of_family(AdapterFamily.STT)
    slot.load(adapter, AdapterProgressBuilder(RecordingSink()).build())

    slot.load(adapter, AdapterProgressBuilder(sink).build())

    assert (adapter.held, sink.events) == (True, [])


def test_emptying_the_slot_releases_the_held_model() -> None:
    sink = RecordingSink()
    slot = ModelSlot()
    adapter = of_family(AdapterFamily.STT)
    slot.load(adapter, AdapterProgressBuilder(RecordingSink()).build())

    slot.empty(AdapterProgressBuilder(sink).build())

    assert (adapter.held, [e.event for e in sink.events]) == (False, ["model_released"])


def test_emptying_an_empty_slot_logs_nothing() -> None:
    sink = RecordingSink()

    ModelSlot().empty(AdapterProgressBuilder(sink).build())

    assert sink.events == []
