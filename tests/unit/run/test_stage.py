import contextlib

from pyrobardfx.events.fan_out import EventFanOut
from pyrobardfx.run.cancel import RunCancelledError
from pyrobardfx.run.constants import STAGE_ORDER
from pyrobardfx.run.pipeline import NoOpStage, Pipeline
from pyrobardfx.run.snapshot import RunSnapshotBuilder
from pyrobardfx.run.stage import StageDependencies
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
        .run_id("20261109T153000Z-a1b2")
        .build(),
        events=EventFanOut(clock, (sink or RecordingSink(),)),
        clock=clock,
        cancel=cancel or FakeCancelToken(),
    )


def test_a_no_op_stage_returns_its_inputs_unchanged() -> None:
    inputs = ("transcript", 3)

    assert NoOpStage[tuple[str, int]]("settings", dependencies()).run(inputs) is inputs


def test_a_pipeline_hands_each_stage_the_value_the_stage_before_returned() -> None:
    shared = dependencies()
    stages = (
        FakeStage("settings", shared),
        NoOpStage[tuple[str, ...]]("snapshot", shared),
        FakeStage("upscale", shared),
    )

    assert Pipeline(stages).run(("start",)) == ("start", "settings", "upscale")


def test_the_harness_pipeline_passes_its_value_through_every_no_op_stage() -> None:
    value = ("transcript",)

    assert Pipeline[tuple[str, ...]].harness(dependencies()).run(value) is value


def test_the_harness_pipeline_runs_its_first_stages_before_the_harness_order() -> None:
    sink = RecordingSink()
    shared = dependencies(sink=sink)

    Pipeline.harness(shared, FakeStage("prune_runs", shared)).run(())

    started = [event.stage for event in sink.events if event.event == "stage_started"]
    assert started == ["prune_runs", *STAGE_ORDER]


def test_a_stage_asked_to_stop_before_its_body_does_no_step() -> None:
    stage = FakeStage("render_in_chunks", dependencies(FakeCancelToken(cancel_at=1)))

    with contextlib.suppress(RunCancelledError):
        stage.run(())

    assert stage.done == []


def test_a_stage_asked_to_stop_between_steps_stops_at_the_next_check() -> None:
    stage = FakeStage("render_in_chunks", dependencies(FakeCancelToken(cancel_at=2)))

    with contextlib.suppress(RunCancelledError):
        stage.run(())

    assert stage.done == ["first"]


def test_a_stage_that_stops_logs_one_cancel_event_with_its_stage_and_percent() -> None:
    sink = RecordingSink()
    stage = FakeStage("render_in_chunks", dependencies(FakeCancelToken(cancel_at=2), sink))

    with contextlib.suppress(RunCancelledError):
        stage.run(())

    cancelled = [(e.stage, e.percent) for e in sink.events if e.event == "run_cancelled"]
    assert cancelled == [("render_in_chunks", 50.0)]
