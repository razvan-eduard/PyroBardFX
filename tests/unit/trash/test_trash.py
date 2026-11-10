import errno
from pathlib import Path

from pyrobardfx.events.fan_out import StageEvents
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.clock import START, FakeClock
from tests.fakes.events import RecordingSink
from tests.fakes.trash import FakeTrash


def events_of_pruning(sink: RecordingSink) -> StageEvents:
    return FanOutBuilder.over(FakeClock(START), (sink,)).at("prune_runs")


def old_run(sandbox: Path) -> Path:
    folder = sandbox / "runs" / "20261109T153000Z-a1b2"
    folder.mkdir(parents=True)
    return folder


def test_a_trashed_path_is_logged_once_with_its_path(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")

    sink = RecordingSink()

    trash.trash(folder, events_of_pruning(sink))

    assert [(e.event, e.fields["path"]) for e in sink.events] == [("path_trashed", str(folder))]


def test_a_trashed_path_event_carries_how_long_the_move_took(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash", seconds_per_move=1.5)

    sink = RecordingSink()

    trash.trash(folder, events_of_pruning(sink))

    assert [e.fields["seconds"] for e in sink.events] == [1.5]


def test_a_path_the_trash_refuses_is_logged_with_its_path_and_the_os_reason(
    tmp_path: Path,
) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")
    trash.refuse(folder, PermissionError(errno.EACCES, "Permission denied", str(folder)))

    sink = RecordingSink()

    trash.trash(folder, events_of_pruning(sink))

    assert [(e.event, e.fields["path"], e.fields["reason"]) for e in sink.events] == [
        ("path_not_trashed", str(folder), "Permission denied")
    ]


def test_a_trash_event_carries_the_stage_of_its_caller_and_percent(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")

    sink = RecordingSink()

    trash.trash(folder, events_of_pruning(sink))

    assert [(e.stage, e.percent) for e in sink.events] == [("prune_runs", 100.0)]


def test_a_refused_trash_event_carries_the_stage_of_its_caller_and_percent(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")
    trash.refuse(folder, PermissionError(errno.EACCES, "Permission denied", str(folder)))

    sink = RecordingSink()

    trash.trash(folder, events_of_pruning(sink))

    assert [(e.stage, e.percent) for e in sink.events] == [("prune_runs", 100.0)]


def test_a_refusal_without_an_errno_is_logged_with_the_os_message(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")
    trash.refuse(folder, OSError("Finder could not move the item"))

    sink = RecordingSink()

    trash.trash(folder, events_of_pruning(sink))

    assert [e.fields["reason"] for e in sink.events] == ["Finder could not move the item"]
