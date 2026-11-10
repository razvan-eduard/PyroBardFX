import contextlib

from pyrobardfx.adapters.constants import Backend
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.domain.constants import StageName
from pyrobardfx.domain.run_id import RunId
from pyrobardfx.run.cancel import RunCancelledError
from pyrobardfx.run.constants import STAGE_ORDER
from pyrobardfx.run.pipeline import NoOpStage, Pipeline
from pyrobardfx.run.snapshot import RunSnapshotBuilder
from pyrobardfx.run.stage import StageDependencies
from pyrobardfx.settings.model import Settings
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink
from tests.fakes.stages import FakeStage


def dependencies(
    cancel: FakeCancelToken | None = None, sink: RecordingSink | None = None
) -> StageDependencies:
    clock = FakeClock()
    return StageDependencies(
        snapshot=RunSnapshotBuilder()
        .story("the-lighthouse")
        .run_id(RunId("20261109T153000Z-a1b2"))
        .settings(Settings())
        .backend_order(BackendOrder((Backend.CPU,)))
        .build(),
        events=FanOutBuilder.over(clock, (sink or RecordingSink(),)),
        clock=clock,
        cancel=cancel or FakeCancelToken(),
    )


def test_a_no_op_stage_returns_its_inputs_unchanged() -> None:
    inputs = ("transcript", 3)

    assert NoOpStage[tuple[str, int]](StageName.SETTINGS, dependencies()).run(inputs) is inputs


def test_a_pipeline_hands_each_stage_the_value_the_stage_before_returned() -> None:
    shared = dependencies()
    stages = (
        FakeStage(StageName.SETTINGS, shared),
        NoOpStage[tuple[str, ...]](StageName.SNAPSHOT, shared),
        FakeStage(StageName.UPSCALE, shared),
    )

    assert Pipeline(stages).run(("start",)) == ("start", "settings", "upscale")


def test_the_harness_pipeline_passes_its_value_through_every_no_op_stage() -> None:
    value = ("transcript",)

    assert Pipeline[tuple[str, ...]].harness(dependencies()).run(value) is value


def test_the_harness_pipeline_runs_its_first_stages_before_the_harness_order() -> None:
    sink = RecordingSink()
    shared = dependencies(sink=sink)

    Pipeline.harness(shared, FakeStage(StageName.PRUNE_RUNS, shared)).run(())

    started = [event.stage for event in sink.events if event.event == "stage_started"]
    assert started == ["prune_runs", *STAGE_ORDER]


def test_a_stage_asked_to_stop_before_its_body_does_no_step() -> None:
    stage = FakeStage(StageName.RENDER_IN_CHUNKS, dependencies(FakeCancelToken(cancel_at=1)))

    with contextlib.suppress(RunCancelledError):
        stage.run(())

    assert stage.done == []


def test_a_stage_asked_to_stop_between_steps_stops_at_the_next_check() -> None:
    stage = FakeStage(StageName.RENDER_IN_CHUNKS, dependencies(FakeCancelToken(cancel_at=2)))

    with contextlib.suppress(RunCancelledError):
        stage.run(())

    assert stage.done == ["first"]


def test_a_stage_that_stops_logs_one_cancel_event_with_its_stage_and_percent() -> None:
    sink = RecordingSink()
    stage = FakeStage(StageName.RENDER_IN_CHUNKS, dependencies(FakeCancelToken(cancel_at=2), sink))

    with contextlib.suppress(RunCancelledError):
        stage.run(())

    cancelled = [(e.stage, e.percent) for e in sink.events if e.event == "run_cancelled"]
    assert cancelled == [("render_in_chunks", 50.0)]


def test_the_harness_pipeline_runs_a_given_stage_in_the_place_of_its_same_name_no_op() -> None:
    sink = RecordingSink()
    shared = dependencies(sink=sink)
    stages = (FakeStage(StageName.PRUNE_RUNS, shared), FakeStage(StageName.SETTINGS, shared))

    value = Pipeline.harness(shared, *stages).run(())

    started = [event.stage for event in sink.events if event.event == "stage_started"]
    assert (value, started) == (("prune_runs", "settings"), ["prune_runs", *STAGE_ORDER])
