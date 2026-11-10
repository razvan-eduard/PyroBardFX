import errno
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from tests.builders.cli_app import CliAppBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import START, FakeClock
from tests.fakes.tokens import FixedTokenSource
from tests.fakes.trash import FakeTrash

STORY = "the-lighthouse"
RUN_ID = "20261109T153000Z-a1b2"


def run_story(
    sandbox: Path,
    clock: FakeClock,
    story: str = STORY,
    working: WorkingDirectoryBuilder | None = None,
    tokens: FixedTokenSource | None = None,
    trash: FakeTrash | None = None,
    cancel: FakeCancelToken | None = None,
) -> Result:
    root = (working or WorkingDirectoryBuilder(sandbox / "work")).story(STORY).build()
    app = CliAppBuilder(sandbox).clock(clock).tokens(tokens or FixedTokenSource("a1b2"))
    app = app.trash(trash or FakeTrash(clock, sandbox / "trash")).cancel(
        cancel or FakeCancelToken()
    )
    return CliRunner().invoke(app.build(), ["--working-dir", str(root), "run", story])


def log_of(sandbox: Path) -> list[dict[str, object]]:
    lines = (runs_of(sandbox) / RUN_ID / "run.log").read_text().splitlines()
    return [json.loads(line) for line in lines]


def runs_of(sandbox: Path) -> Path:
    return sandbox / "work" / "stories" / STORY / "runs"


def test_a_run_writes_a_run_folder_named_by_its_utc_time_and_token(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START))

    assert [folder.name for folder in runs_of(tmp_path).iterdir()] == ["20261109T153000Z-a1b2"]


def test_a_run_id_is_stamped_in_utc_when_the_clock_reports_another_zone(tmp_path: Path) -> None:
    bucharest = timezone(timedelta(hours=2))
    run_story(tmp_path, FakeClock(datetime(2026, 11, 9, 17, 30, 0, tzinfo=bucharest)))

    assert [folder.name for folder in runs_of(tmp_path).iterdir()] == ["20261109T153000Z-a1b2"]


def test_a_run_folder_holds_the_snapshot_the_run_started_with(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START))

    snapshot = json.loads((runs_of(tmp_path) / RUN_ID / "snapshot.json").read_text())
    assert (snapshot["story"], snapshot["run_id"], snapshot["runs_to_keep"]) == (STORY, RUN_ID, 5)


def test_a_run_prunes_then_passes_every_stage_in_the_harness_order(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START))

    finished = [event["stage"] for event in log_of(tmp_path) if event["event"] == "stage_finished"]
    assert finished == [
        "prune_runs",
        "working_directory_open",
        "settings",
        "tagging_or_reconcile",
        "snapshot",
        "voice_and_alignment",
        "sound_design_and_mix",
        "scenes_and_look",
        "final_script_and_review",
        "render_in_chunks",
        "audio_reactive_fx",
        "upscale",
        "mux_and_subtitles",
        "export_per_video",
    ]


def test_the_story_latest_pointer_names_the_newest_run(tmp_path: Path) -> None:
    clock = FakeClock(START)
    run_story(tmp_path, clock)
    clock.advance(60)
    run_story(tmp_path, clock)

    latest = json.loads((tmp_path / "work" / "stories" / STORY / "latest.json").read_text())
    assert latest == {"run_id": "20261109T153100Z-a1b2"}


def run_six_times(
    sandbox: Path, working: WorkingDirectoryBuilder, trash: FakeTrash | None = None
) -> Result:
    clock = FakeClock(START)
    for _ in range(5):
        run_story(sandbox, clock, working=working, trash=trash)
        clock.advance(60)
    return run_story(sandbox, clock, working=working, trash=trash)


def test_a_run_start_prunes_the_oldest_runs_down_to_the_keep_count_of_five(
    tmp_path: Path,
) -> None:
    run_six_times(tmp_path, WorkingDirectoryBuilder(tmp_path / "work"))

    assert sorted(folder.name for folder in runs_of(tmp_path).iterdir()) == [
        "20261109T153100Z-a1b2",
        "20261109T153200Z-a1b2",
        "20261109T153300Z-a1b2",
        "20261109T153400Z-a1b2",
        "20261109T153500Z-a1b2",
    ]


def test_a_pruned_run_folder_goes_to_the_trash_instead_of_being_deleted(tmp_path: Path) -> None:
    run_six_times(tmp_path, WorkingDirectoryBuilder(tmp_path / "work"))

    assert [folder.name for folder in (tmp_path / "trash").iterdir()] == ["20261109T153000Z-a1b2"]


def refusing_trash(sandbox: Path) -> FakeTrash:
    trash = FakeTrash(FakeClock(START), sandbox / "trash")
    trash.refuse(
        runs_of(sandbox) / RUN_ID,
        PermissionError(errno.EACCES, "Permission denied", str(runs_of(sandbox) / RUN_ID)),
    )
    return trash


def test_an_old_run_the_trash_refuses_stays_in_runs(tmp_path: Path) -> None:
    run_six_times(tmp_path, WorkingDirectoryBuilder(tmp_path / "work"), refusing_trash(tmp_path))

    assert (runs_of(tmp_path) / RUN_ID).is_dir()


def test_a_run_still_starts_when_the_trash_refuses_an_old_run(tmp_path: Path) -> None:
    result = run_six_times(
        tmp_path, WorkingDirectoryBuilder(tmp_path / "work"), refusing_trash(tmp_path)
    )

    assert (result.exit_code, (runs_of(tmp_path) / "20261109T153500Z-a1b2").is_dir()) == (0, True)


def test_a_run_cancelled_before_its_first_stage_trashes_no_old_run(tmp_path: Path) -> None:
    clock = FakeClock(START)
    for _ in range(5):
        run_story(tmp_path, clock)
        clock.advance(60)

    run_story(tmp_path, clock, cancel=FakeCancelToken(cancel_at=1))

    assert len(list(runs_of(tmp_path).iterdir())) == 6


def test_a_folder_in_runs_that_is_not_a_run_folder_is_never_pruned(tmp_path: Path) -> None:
    run_six_times(tmp_path, WorkingDirectoryBuilder(tmp_path / "work").run_folder(STORY, "0-draft"))

    assert (runs_of(tmp_path) / "0-draft").is_dir()


def test_a_folder_that_is_not_a_run_folder_never_takes_the_place_of_a_kept_run(
    tmp_path: Path,
) -> None:
    run_six_times(tmp_path, WorkingDirectoryBuilder(tmp_path / "work").run_folder(STORY, "notes"))

    assert len([name for name in runs_of(tmp_path).iterdir() if name.name != "notes"]) == 5


def test_a_run_of_a_story_that_does_not_exist_is_refused_with_its_reason(tmp_path: Path) -> None:
    result = run_story(tmp_path, FakeClock(START), story="the-lost-ship")

    assert "no Story named the-lost-ship" in result.output


def test_a_refused_run_exits_with_a_failure_code(tmp_path: Path) -> None:
    result = run_story(tmp_path, FakeClock(START), story="the-lost-ship")

    assert result.exit_code == 1


def test_a_refused_run_creates_no_story_folder(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START), story="the-lost-ship")

    assert not (tmp_path / "work" / "stories" / "the-lost-ship").exists()


@pytest.mark.parametrize("name", ["..", ".", "the-lighthouse/runs"])
def test_a_story_name_that_is_not_one_folder_under_stories_is_refused(
    tmp_path: Path, name: str
) -> None:
    result = run_story(tmp_path, FakeClock(START), story=name)

    assert result.exit_code == 1


def test_a_finished_run_prints_where_its_run_folder_is(tmp_path: Path) -> None:
    result = run_story(tmp_path, FakeClock(START))

    assert str(runs_of(tmp_path) / RUN_ID) in result.stdout


def test_a_run_whose_id_is_already_taken_deletes_no_earlier_run(tmp_path: Path) -> None:
    clock = FakeClock(START)
    for _ in range(5):
        clock.advance(60)
        run_story(tmp_path, clock)

    run_story(tmp_path, clock)

    assert len(list(runs_of(tmp_path).iterdir())) == 5


def test_a_run_whose_drawn_id_is_taken_draws_new_tokens_up_to_three_times(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START))

    run_story(tmp_path, FakeClock(START), tokens=FixedTokenSource("a1b2", "a1b2", "c3d4"))

    assert (runs_of(tmp_path) / "20261109T153000Z-c3d4").is_dir()


def test_a_run_whose_three_drawn_ids_are_all_taken_is_refused_with_its_reason(
    tmp_path: Path,
) -> None:
    run_story(tmp_path, FakeClock(START))

    result = run_story(
        tmp_path, FakeClock(START), tokens=FixedTokenSource("a1b2", "a1b2", "a1b2", "c3d4")
    )

    assert "already has a Run folder" in result.output


def test_a_cancelled_run_leaves_its_run_folder_whole(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START), cancel=FakeCancelToken(cancel_at=4))

    assert sorted(path.name for path in (runs_of(tmp_path) / RUN_ID).iterdir()) == [
        "run.log",
        "snapshot.json",
    ]


def test_a_cancelled_run_passes_no_stage_after_the_one_that_stopped(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START), cancel=FakeCancelToken(cancel_at=4))

    finished = [event["stage"] for event in log_of(tmp_path) if event["event"] == "stage_finished"]
    assert finished == ["prune_runs", "working_directory_open", "settings"]


def test_a_cancelled_run_logs_its_cancel_event_in_its_run_log(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START), cancel=FakeCancelToken(cancel_at=4))

    cancelled = [event["stage"] for event in log_of(tmp_path) if event["event"] == "run_cancelled"]
    assert cancelled == ["tagging_or_reconcile"]


def test_a_cancelled_run_prints_that_it_was_cancelled(tmp_path: Path) -> None:
    result = run_story(tmp_path, FakeClock(START), cancel=FakeCancelToken(cancel_at=4))

    assert f"Run {RUN_ID} cancelled" in result.stdout


def test_a_cancelled_run_exits_with_the_cancelled_code(tmp_path: Path) -> None:
    result = run_story(tmp_path, FakeClock(START), cancel=FakeCancelToken(cancel_at=4))

    assert result.exit_code == 130


def test_every_run_log_line_carries_the_clock_time_in_utc(tmp_path: Path) -> None:
    run_story(tmp_path, FakeClock(START))

    assert {event["timestamp"] for event in log_of(tmp_path)} == {"2026-11-09T15:30:00Z"}


def test_a_pruned_run_is_logged_in_the_new_runs_log_under_the_pruning_stage(
    tmp_path: Path,
) -> None:
    run_six_times(tmp_path, WorkingDirectoryBuilder(tmp_path / "work"))

    lines = (runs_of(tmp_path) / "20261109T153500Z-a1b2" / "run.log").read_text().splitlines()
    trashed = [json.loads(line) for line in lines if "path_trashed" in line]
    assert [(event["stage"], event["fields"]["path"]) for event in trashed] == [
        ("prune_runs", str(runs_of(tmp_path) / RUN_ID))
    ]


def test_a_run_prints_its_stage_events_on_stderr(tmp_path: Path) -> None:
    result = run_story(tmp_path, FakeClock(START))

    assert "export_per_video 100% stage_finished" in result.stderr
