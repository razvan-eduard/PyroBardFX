import io
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from pyrobardfx.events.event import PipelineEvent
from pyrobardfx.events.fan_out import EventFanOut
from tests.fakes.clock import START, FakeClock
from tests.fakes.events import RecordingSink


def test_an_event_is_stamped_in_utc_with_the_clock_time() -> None:
    sink = RecordingSink()
    clock = FakeClock(datetime(2026, 11, 9, 17, 30, 0, tzinfo=timezone(timedelta(hours=2))))

    EventFanOut(clock, (sink,)).at("settings").emit("stage_started", 0.0)

    assert [event.timestamp.isoformat() for event in sink.events] == ["2026-11-09T15:30:00+00:00"]


def test_an_event_whose_timestamp_is_not_in_utc_is_refused() -> None:
    bucharest = datetime(2026, 11, 9, 17, 30, 0, tzinfo=timezone(timedelta(hours=2)))

    with pytest.raises(ValidationError):
        PipelineEvent(event="stage_started", stage="settings", percent=0.0, timestamp=bucharest)


def test_an_event_with_a_percent_above_one_hundred_is_refused() -> None:
    fan_out = EventFanOut(FakeClock(), (RecordingSink(),))

    with pytest.raises(ValidationError):
        fan_out.at("settings").emit("stage_finished", 100.5)


def test_one_event_reaches_every_sink_including_one_added_later() -> None:
    first, later = RecordingSink(), RecordingSink()

    EventFanOut(FakeClock(), (first,)).with_sink(later).at("settings").emit("stage_started", 0)

    assert [len(first.events), len(later.events)] == [1, 1]


def test_an_event_carries_its_own_fields_beside_event_stage_and_percent() -> None:
    sink = RecordingSink()

    EventFanOut(FakeClock(), (sink,)).at("prune_runs").emit("path_trashed", 100.0, seconds=1.5)

    event = sink.events[0]
    assert (event.event, event.stage, event.percent, event.timestamp, event.fields) == (
        "path_trashed",
        "prune_runs",
        100.0,
        START,
        {"seconds": 1.5},
    )


def emit_twice(fan_out: EventFanOut) -> None:
    events = fan_out.at("settings")
    events.emit("stage_started", 0.0)
    events.emit("stage_finished", 100.0)


def test_a_failing_sink_leaves_every_other_sink_its_events() -> None:
    other = RecordingSink()

    emit_twice(
        EventFanOut(FakeClock(), (RecordingSink(OSError("disk full")), other), io.StringIO())
    )

    assert len(other.events) == 2


def test_a_failing_sink_is_skipped_after_its_first_failure() -> None:
    failing = RecordingSink(OSError("disk full"))

    emit_twice(EventFanOut(FakeClock(), (failing,), io.StringIO()))

    assert len(failing.events) == 1


def test_a_failing_sink_is_reported_once_on_the_error_stream_with_its_reason() -> None:
    errors = io.StringIO()

    emit_twice(EventFanOut(FakeClock(), (RecordingSink(OSError("disk full")),), errors))

    assert errors.getvalue().count("disk full") == 1
