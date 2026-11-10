from types import MappingProxyType

import pytest

from pyrobardfx.adapters.base import AdapterDeclaration, AdapterProgress
from pyrobardfx.adapters.constants import AdapterFamily, Backend, DType
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.domain.constants import StageName
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.cancel import RunCancelledError
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.adapter import FakeAdapter
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink

APPLE_SILICON = BackendOrder((Backend.MLX, Backend.MPS, Backend.CPU))
CPU_ONLY = BackendOrder((Backend.CPU,))
EVERY_BACKEND = (Backend.MLX, Backend.MPS, Backend.CUDA, Backend.CPU)


def progress_into(sink: RecordingSink, cancel: FakeCancelToken | None = None) -> AdapterProgress:
    """The progress of a stage whose events go to `sink` and whose cancel check asks `cancel`."""
    token = cancel or FakeCancelToken()

    def check_cancel(percent: float) -> None:
        if token.is_cancelled():
            raise RunCancelledError(StageName.SETTINGS)

    events = FanOutBuilder.over(FakeClock(), (sink,)).at(StageName.SETTINGS)
    return AdapterProgress(events, check_cancel)


def declaring(family: AdapterFamily, *backends: Backend) -> AdapterDeclaration:
    return AdapterDeclaration(family, MappingProxyType(dict.fromkeys(backends, DType.FLOAT16)))


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


@pytest.mark.parametrize(
    "family", [AdapterFamily.STT, AdapterFamily.TTS, AdapterFamily.LLM, AdapterFamily.CLAP]
)
def test_on_the_cpu_transcription_voice_tagging_and_matching_still_run(
    family: AdapterFamily,
) -> None:
    adapter = FakeAdapter(CPU_ONLY, FakeClock(), declaring(family, *EVERY_BACKEND))

    assert adapter.backend is Backend.CPU


def test_an_adapter_declaring_none_of_the_order_is_refused_naming_family_and_order() -> None:
    with pytest.raises(RefusedError) as refused:
        FakeAdapter(APPLE_SILICON, FakeClock(), declaring(AdapterFamily.STT, Backend.CUDA))

    assert (refused.value.reason, refused.value.detail) == (
        RefusalReason.BACKEND_UNSUPPORTED,
        "stt: mlx > mps > cpu",
    )


def test_a_load_is_logged_with_family_backend_dtype_and_the_seconds_it_took() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock(), seconds_to_load=2.5)

    adapter.load(progress_into(sink))

    assert [(e.event, e.fields) for e in sink.events] == [
        (
            "model_loaded",
            {"family": "stt", "backend": "mlx", "dtype": "float16", "seconds": 2.5},
        )
    ]


def test_loading_a_loaded_adapter_again_loads_nothing_and_logs_nothing() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())
    adapter.load(progress_into(RecordingSink()))

    adapter.load(progress_into(sink))

    assert sink.events == []


def test_a_release_frees_the_model_and_is_logged_with_the_seconds_it_took() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock(), seconds_to_release=0.5)
    adapter.load(progress_into(RecordingSink()))

    adapter.release(progress_into(sink))

    assert (adapter.held, [(e.event, e.fields) for e in sink.events]) == (
        False,
        [("model_released", {"family": "stt", "backend": "mlx", "seconds": 0.5})],
    )


def test_releasing_an_adapter_that_holds_no_model_logs_nothing() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    adapter.release(progress_into(sink))

    assert sink.events == []


def test_a_load_asked_to_stop_raises_before_the_model_is_in_memory() -> None:
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    with pytest.raises(RunCancelledError):
        adapter.load(progress_into(RecordingSink(), FakeCancelToken(cancel_at=1)))

    assert adapter.held is False


def test_each_step_is_logged_with_its_percent_and_fields() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    adapter.work(progress_into(sink), steps=2)

    assert [(e.event, e.percent, e.fields) for e in sink.events] == [
        ("model_step", 50.0, {"step": 1}),
        ("model_step", 100.0, {"step": 2}),
    ]


def test_a_run_asked_to_stop_stops_the_adapter_at_its_next_step() -> None:
    sink = RecordingSink()
    adapter = FakeAdapter(APPLE_SILICON, FakeClock())

    with pytest.raises(RunCancelledError):
        adapter.work(progress_into(sink, FakeCancelToken(cancel_at=2)), steps=3)

    assert [e.fields["step"] for e in sink.events] == [1]
