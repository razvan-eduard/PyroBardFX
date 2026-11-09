import errno
from datetime import UTC, datetime
from pathlib import Path

import structlog

from tests.fakes.clock import FakeClock
from tests.fakes.trash import FakeTrash

START = datetime(2026, 11, 9, 15, 30, 0, tzinfo=UTC)


def old_run(sandbox: Path) -> Path:
    folder = sandbox / "runs" / "20261109T153000Z-a1b2"
    folder.mkdir(parents=True)
    return folder


def test_a_trashed_path_is_logged_once_with_its_path(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")

    with structlog.testing.capture_logs() as events:
        trash.trash(folder)

    assert [(e["event"], e["path"]) for e in events] == [("path_trashed", str(folder))]


def test_a_trashed_path_event_carries_how_long_the_move_took(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash", seconds_per_move=1.5)

    with structlog.testing.capture_logs() as events:
        trash.trash(folder)

    assert [e["seconds"] for e in events] == [1.5]


def test_a_path_the_trash_refuses_is_logged_with_its_path_and_the_os_reason(
    tmp_path: Path,
) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")
    trash.refuse(folder, PermissionError(errno.EACCES, "Permission denied", str(folder)))

    with structlog.testing.capture_logs() as events:
        trash.trash(folder)

    assert [(e["event"], e["path"], e["reason"]) for e in events] == [
        ("path_not_trashed", str(folder), "Permission denied")
    ]


def test_a_trash_event_carries_its_stage_and_percent(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")

    with structlog.testing.capture_logs() as events:
        trash.trash(folder)

    assert [(e.get("stage"), e.get("percent")) for e in events] == [("trash", 100.0)]


def test_a_refused_trash_event_carries_its_stage_and_percent(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")
    trash.refuse(folder, PermissionError(errno.EACCES, "Permission denied", str(folder)))

    with structlog.testing.capture_logs() as events:
        trash.trash(folder)

    assert [(e.get("stage"), e.get("percent")) for e in events] == [("trash", 100.0)]


def test_a_refusal_without_an_errno_is_logged_with_the_os_message(tmp_path: Path) -> None:
    folder = old_run(tmp_path)
    trash = FakeTrash(FakeClock(START), tmp_path / "trash")
    trash.refuse(folder, OSError("Finder could not move the item"))

    with structlog.testing.capture_logs() as events:
        trash.trash(folder)

    assert [e["reason"] for e in events] == ["Finder could not move the item"]
