from pathlib import Path

from pyrobardfx.events.fan_out import EventFanOut
from pyrobardfx.run.settings_stage import SettingsStage
from pyrobardfx.run.snapshot import RunSnapshotBuilder
from pyrobardfx.run.stage import StageDependencies
from pyrobardfx.settings.service import SettingsService
from pyrobardfx.workdir.run_folders import RunFolder
from pyrobardfx.workdir.working_directory import WorkingDirectory
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink

RUN_ID = "20261109T153000Z-a1b2"


def dependencies(sink: RecordingSink) -> StageDependencies:
    clock = FakeClock()
    return StageDependencies(
        snapshot=RunSnapshotBuilder().story("the-lighthouse").run_id(RUN_ID).build(),
        events=EventFanOut(clock, (sink,)),
        clock=clock,
        cancel=FakeCancelToken(),
    )


def settings_with_broken_file(root: Path) -> tuple[SettingsService, Path]:
    path = root / "config" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"runs_to_keep": "many"}', encoding="utf-8")
    clock = FakeClock()
    service = SettingsService.open(WorkingDirectory(root=root), clock, EventFanOut(clock, ()))
    return service, path


def test_the_settings_stage_replays_each_set_aside_file_between_its_start_and_finish(
    tmp_path: Path,
) -> None:
    settings, path = settings_with_broken_file(tmp_path)
    sink = RecordingSink()
    stage = SettingsStage("settings", dependencies(sink), settings)

    stage.run(RunFolder(RUN_ID, tmp_path / RUN_ID))

    assert [(event.event, event.stage, event.fields) for event in sink.events] == [
        ("stage_started", "settings", {}),
        (
            "settings_file_set_aside",
            "settings",
            {
                "path": str(path),
                "backup": str(path.with_name("settings.broken-20261109T153000Z.json")),
            },
        ),
        ("stage_finished", "settings", {}),
    ]


def test_the_settings_stage_returns_its_run_folder_unchanged(tmp_path: Path) -> None:
    settings, _ = settings_with_broken_file(tmp_path)
    folder = RunFolder(RUN_ID, tmp_path / RUN_ID)

    assert SettingsStage("settings", dependencies(RecordingSink()), settings).run(folder) is folder
