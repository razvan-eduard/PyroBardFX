import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from pyrobardfx.domain.constants import StageName
from pyrobardfx.events.event import PipelineEvent
from pyrobardfx.events.fan_out import EventFanOut
from pyrobardfx.locales.constants import Language
from pyrobardfx.locales.labels import Labels
from tests.builders.locales import LocalesBuilder
from tests.fakes.clock import START, FakeClock
from tests.fakes.events import RecordingSink

# The repo's own en labels: every test here not about the report's language reads them.
ENGLISH = Labels.load(Language.EN)


def test_an_event_is_stamped_in_utc_with_the_clock_time() -> None:
    sink = RecordingSink()
    clock = FakeClock(datetime(2026, 11, 9, 17, 30, 0, tzinfo=timezone(timedelta(hours=2))))

    EventFanOut(clock, (sink,), io.StringIO(), ENGLISH).at(StageName.SETTINGS).emit(
        "stage_started", 0.0
    )

    assert [event.timestamp.isoformat() for event in sink.events] == ["2026-11-09T15:30:00+00:00"]


def test_an_event_whose_timestamp_is_not_in_utc_is_refused() -> None:
    bucharest = datetime(2026, 11, 9, 17, 30, 0, tzinfo=timezone(timedelta(hours=2)))

    with pytest.raises(ValidationError):
        PipelineEvent(
            event="stage_started", stage=StageName.SETTINGS, percent=0.0, timestamp=bucharest
        )


def test_an_event_with_a_percent_above_one_hundred_is_refused() -> None:
    fan_out = EventFanOut(FakeClock(), (RecordingSink(),), io.StringIO(), ENGLISH)

    with pytest.raises(ValidationError):
        fan_out.at(StageName.SETTINGS).emit("stage_finished", 100.5)


def test_one_event_reaches_every_sink_including_one_added_later() -> None:
    first, later = RecordingSink(), RecordingSink()

    EventFanOut(FakeClock(), (first,), io.StringIO(), ENGLISH).with_sink(later).at(
        StageName.SETTINGS
    ).emit("stage_started", 0)

    assert [len(first.events), len(later.events)] == [1, 1]


def test_an_event_carries_its_own_fields_beside_event_stage_and_percent() -> None:
    sink = RecordingSink()

    EventFanOut(FakeClock(), (sink,), io.StringIO(), ENGLISH).at(StageName.PRUNE_RUNS).emit(
        "path_trashed", 100.0, seconds=1.5
    )

    event = sink.events[0]
    assert (event.event, event.stage, event.percent, event.timestamp, event.fields) == (
        "path_trashed",
        "prune_runs",
        100.0,
        START,
        {"seconds": 1.5},
    )


def emit_twice(fan_out: EventFanOut) -> None:
    events = fan_out.at(StageName.SETTINGS)
    events.emit("stage_started", 0.0)
    events.emit("stage_finished", 100.0)


def test_a_failing_sink_leaves_every_other_sink_its_events() -> None:
    other = RecordingSink()

    emit_twice(
        EventFanOut(
            FakeClock(), (RecordingSink(OSError("disk full")), other), io.StringIO(), ENGLISH
        )
    )

    assert len(other.events) == 2


def test_a_failing_sink_is_skipped_after_its_first_failure() -> None:
    failing = RecordingSink(OSError("disk full"))

    emit_twice(EventFanOut(FakeClock(), (failing,), io.StringIO(), ENGLISH))

    assert len(failing.events) == 1


def test_a_failing_sink_is_reported_once_on_the_error_stream_with_its_reason() -> None:
    errors = io.StringIO()

    emit_twice(EventFanOut(FakeClock(), (RecordingSink(OSError("disk full")),), errors, ENGLISH))

    assert errors.getvalue().count("disk full") == 1


def test_a_failing_sink_is_reported_in_the_language_of_the_labels(tmp_path: Path) -> None:
    folder = (
        LocalesBuilder(tmp_path)
        .texts(Language.EN, {})
        .texts(Language.RO, {"events.sink_failed": "Receptorul {sink} a cedat: {reason}"})
    )
    errors = io.StringIO()
    failing = RecordingSink(OSError("disk full"))

    emit_twice(
        EventFanOut(FakeClock(), (failing,), errors, Labels.load(Language.RO, folder.build()))
    )

    assert "a cedat" in errors.getvalue()
