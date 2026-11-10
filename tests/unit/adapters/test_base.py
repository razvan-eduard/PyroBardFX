from types import MappingProxyType

import pytest

from pyrobardfx.adapters.base import AdapterDeclaration
from pyrobardfx.adapters.constants import AdapterFamily, Backend, DType
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.cancel import RunCancelledError
from tests.builders.adapter_progress import AdapterProgressBuilder
from tests.fakes.adapter import FakeAdapter
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink

APPLE_SILICON = BackendOrder((Backend.MLX, Backend.MPS, Backend.CPU))
CPU_ONLY = BackendOrder((Backend.CPU,))
EVERY_BACKEND = (Backend.MLX, Backend.MPS, Backend.CUDA, Backend.CPU)


def declaring(family: AdapterFamily, *backends: Backend) -> AdapterDeclaration:
    return AdapterDeclaration(family, MappingProxyType(dict.fromkeys(backends, DType.FLOAT16)))


def test_a_declaration_keeps_its_dtypes_when_the_dict_it_was_given_changes() -> None:
    dtypes = {Backend.CPU: DType.FLOAT32}
    declaration = AdapterDeclaration(AdapterFamily.STT, dtypes)

    dtypes[Backend.MPS] = DType.FLOAT16

    assert dict(declaration.dtypes) == {Backend.CPU: DType.FLOAT32}


def test_an_adapter_runs_on_the_first_backend_of_the_order_it_declares() -> None:
    adapter = FakeAdapter(
        APPLE_SILICON, FakeClock(), declaring(AdapterFamily.STILL, Backend.MPS, Backend.CPU)
    )

    assert adapter.backend is Backend.MPS


def test_an_adapter_uses_the_dtype_it_declares_for_its_backend() -> None:
    declaration = AdapterDeclaration(
        AdapterFamily.SOUND_GENERATOR,
        MappingProxyType({Backend.MPS: DType.FLOAT32, Backend.CUDA: DType.FLOAT16}),
    )

    adapter = FakeAdapter(APPLE_SILICON, FakeClock(), declaration)

    assert adapter.dtype is DType.FLOAT32


@pytest.mark.parametrize("family", [AdapterFamily.DIFFUSION, AdapterFamily.SOUND_GENERATOR])
def test_on_the_cpu_diffusion_and_sound_generation_are_refused_naming_their_family(
    family: AdapterFamily,
) -> None:
    with pytest.raises(RefusedError) as refused:
        FakeAdapter(CPU_ONLY, FakeClock(), declaring(family, *EVERY_BACKEND))

    assert (refused.value.reason, refused.value.detail) == (RefusalReason.CPU_REFUSED, family)


def test_a_cpu_refusing_family_given_an_accelerator_it_lacks_is_refused_as_unsupported() -> None:
    nvidia = BackendOrder((Backend.CUDA, Backend.CPU))

    with pytest.raises(RefusedError) as refused:
        FakeAdapter(nvidia, FakeClock(), declaring(AdapterFamily.DIFFUSION, Backend.MPS))

    assert refused.value.reason is RefusalReason.BACKEND_UNSUPPORTED


@pytest.mark.parametrize(
    "family", [AdapterFamily.STT, AdapterFamily.TTS, AdapterFamily.LLM, AdapterFamily.CLAP]
)
def test_on_the_cpu_transcription_voice_tagging_and_matching_still_run(
    family: AdapterFamily,
) -> None:
    adapter = FakeAdapter(CPU_ONLY, FakeClock(), declaring(family, *EVERY_BACKEND))

    assert adapter.backend is Backend.CPU


def test_an_adapter_declaring_none_of_the_order_is_refused_naming_the_order_best_first() -> None:
    with pytest.raises(RefusedError) as refused:
        FakeAdapter(APPLE_SILICON, FakeClock(), declaring(AdapterFamily.STT, Backend.CUDA))

    assert (refused.value.reason, refused.value.detail) == (
        RefusalReason.BACKEND_UNSUPPORTED,
        "mlx > mps > cpu",
    )


def test_a_load_is_logged_with_family_backend_dtype_and_the_seconds_it_took() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock(), seconds_to_load=2.5)

    adapter.load(AdapterProgressBuilder(sink).build())

    assert [(e.event, e.fields) for e in sink.events] == [
        (
            "model_loaded",
            {"family": "stt", "backend": "mlx", "dtype": "float16", "seconds": 2.5},
        )
    ]


def test_loading_a_loaded_adapter_again_logs_nothing() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())
    adapter.load(AdapterProgressBuilder(RecordingSink()).build())

    adapter.load(AdapterProgressBuilder(sink).build())

    assert sink.events == []


def test_loading_a_loaded_adapter_again_loads_nothing() -> None:
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())
    adapter.load(AdapterProgressBuilder(RecordingSink()).build())

    adapter.load(AdapterProgressBuilder(RecordingSink()).build())

    assert adapter.loads == 1


def test_a_release_frees_the_model() -> None:
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())
    adapter.load(AdapterProgressBuilder(RecordingSink()).build())

    adapter.release(AdapterProgressBuilder(RecordingSink()).build())

    assert adapter.held is False


def test_a_release_is_logged_with_family_backend_and_the_seconds_it_took() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock(), seconds_to_release=0.5)
    adapter.load(AdapterProgressBuilder(RecordingSink()).build())

    adapter.release(AdapterProgressBuilder(sink).build())

    assert [(e.event, e.fields) for e in sink.events] == [
        ("model_released", {"family": "stt", "backend": "mlx", "seconds": 0.5})
    ]


def test_a_release_collects_the_dropped_model_before_it_flushes_the_accelerator_cache() -> None:
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())
    adapter.load(AdapterProgressBuilder(RecordingSink()).build())

    adapter.release(AdapterProgressBuilder(RecordingSink()).build())

    assert adapter.freed_before_flush is True


def test_releasing_an_adapter_that_holds_no_model_logs_nothing() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    adapter.release(AdapterProgressBuilder(sink).build())

    assert sink.events == []


def test_a_load_asked_to_stop_raises_before_the_model_is_in_memory() -> None:
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    with pytest.raises(RunCancelledError):
        adapter.load(
            AdapterProgressBuilder(RecordingSink()).cancel(FakeCancelToken(cancel_at=1)).build()
        )

    assert adapter.held is False


def test_each_step_is_logged_with_its_percent_and_fields() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    adapter.work(AdapterProgressBuilder(sink).build(), steps=2)

    assert [(e.event, e.percent, e.fields) for e in sink.events] == [
        ("model_step", 50.0, {"step": 1}),
        ("model_step", 100.0, {"step": 2}),
    ]


def test_each_step_is_logged_at_its_percent_of_the_stage_s_span() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    adapter.work(AdapterProgressBuilder(sink).span(20.0, 60.0).build(), steps=2)

    assert [e.percent for e in sink.events] == [40.0, 60.0]


def test_a_load_is_logged_at_the_start_of_the_stage_s_span() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    adapter.load(AdapterProgressBuilder(sink).span(20.0, 60.0).build())

    assert [e.percent for e in sink.events] == [20.0]


def test_a_release_is_logged_at_the_start_of_the_stage_s_span() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())
    adapter.load(AdapterProgressBuilder(RecordingSink()).build())

    adapter.release(AdapterProgressBuilder(sink).span(20.0, 60.0).build())

    assert [e.percent for e in sink.events] == [20.0]


def test_a_run_asked_to_stop_stops_the_adapter_at_its_next_step() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    with pytest.raises(RunCancelledError):
        adapter.work(
            AdapterProgressBuilder(sink).cancel(FakeCancelToken(cancel_at=2)).build(), steps=3
        )

    assert [e.fields["step"] for e in sink.events] == [1]
