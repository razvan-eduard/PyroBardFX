import json
from pathlib import Path

from pyrobardfx.run.service import RunService
from pyrobardfx.settings.model import Settings
from pyrobardfx.settings.service import SettingsService
from pyrobardfx.workdir.working_directory import WorkingDirectory
from tests.builders.fan_out import FanOutBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import START, FakeClock
from tests.fakes.events import RecordingSink
from tests.fakes.tokens import FixedTokenSource
from tests.fakes.trash import FakeTrash

STORY = "the-lighthouse"
RUN_ID = "20261109T153000Z-a1b2"


def test_a_settings_edit_during_a_run_leaves_that_run_on_its_start_settings(
    tmp_path: Path,
) -> None:
    working = WorkingDirectoryBuilder(tmp_path / "work").story(STORY)
    working = working.settings(Settings(runs_to_keep=2))
    for minute in ("00", "10", "20"):
        working.run_folder(STORY, f"20261109T15{minute}00Z-0000")
    root = working.build()
    clock = FakeClock(START)
    settings = SettingsService.open(WorkingDirectory(root=root), clock, FanOutBuilder.over(clock))
    edit = Settings(runs_to_keep=1)
    sink = RecordingSink(on_event=lambda _: settings.write(edit))
    runs = RunService(
        WorkingDirectory(root=root),
        clock,
        FixedTokenSource("a1b2"),
        FakeTrash(clock, tmp_path / "trash"),
        FanOutBuilder.over(clock, (sink,)),
        FakeCancelToken(),
        settings,
    )

    outcome = runs.start(STORY)

    snapshot = json.loads((outcome.folder.path / "snapshot.json").read_text())
    folders = sorted(folder.name for folder in outcome.folder.path.parent.iterdir())
    assert (settings.read(), snapshot["settings"]["runs_to_keep"], folders) == (
        edit,
        2,
        ["20261109T152000Z-0000", RUN_ID],
    )
