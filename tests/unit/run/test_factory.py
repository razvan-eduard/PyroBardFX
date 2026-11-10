from pathlib import Path

import pytest

from pyrobardfx.locales.constants import Language
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.factory import ReadyRun, RunFactory
from pyrobardfx.settings.model import Settings
from pyrobardfx.workdir.working_directory import WorkingDirectory
from tests.builders.locales import LocalesBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import START, FakeClock
from tests.fakes.devices import FakeDeviceProbe
from tests.fakes.events import RecordingSink
from tests.fakes.speaker import RecordingSpeaker
from tests.fakes.tokens import FixedTokenSource
from tests.fakes.trash import FakeTrash

STORY = "the-lighthouse"
RUN_ID = "20261109T153000Z-a1b2"
SET_ASIDE = "settings_file_set_aside"


def ready_run(
    sandbox: Path,
    working: WorkingDirectoryBuilder,
    cancel: FakeCancelToken | None = None,
    sinks: tuple[RecordingSink, ...] = (),
) -> ReadyRun[RecordingSpeaker]:
    """A Run of `working` readied by the factory over fakes, speaking through a recorder."""
    clock = FakeClock(START)
    locales = LocalesBuilder(sandbox / "locales").real(Language.EN)
    labels = Labels.load(Language.EN, locales.texts(Language.RO, {"run.finished": "gata"}).build())
    factory = RunFactory(
        clock,
        FixedTokenSource("a1b2"),
        FakeTrash(clock, sandbox / "trash"),
        cancel or FakeCancelToken(),
        labels,
        FakeDeviceProbe(),
        sinks,
    )
    return factory.open(WorkingDirectory(root=working.build()), RecordingSpeaker)


def with_broken_settings(sandbox: Path) -> WorkingDirectoryBuilder:
    config = sandbox / "work" / "config"
    config.mkdir(parents=True)
    (config / "settings.json").write_text('{"runs_to_keep": "many"}', encoding="utf-8")
    return WorkingDirectoryBuilder(sandbox / "work").story(STORY)


def test_a_readied_run_speaks_the_ui_language_of_the_opened_settings(tmp_path: Path) -> None:
    working = WorkingDirectoryBuilder(tmp_path / "work").story(STORY)
    ready = ready_run(tmp_path, working.settings(Settings(ui_language=Language.RO)))

    assert ready.speaker.labels.label("run.finished") == "gata"


def test_a_readied_run_writes_its_run_folder_and_sends_its_events_to_speaker_and_sinks(
    tmp_path: Path,
) -> None:
    sink = RecordingSink()
    ready = ready_run(
        tmp_path, WorkingDirectoryBuilder(tmp_path / "work").story(STORY), sinks=(sink,)
    )

    outcome = ready.start(STORY)

    assert (outcome.folder.run_id, outcome.cancelled) == (RUN_ID, False)
    assert ready.speaker.events == sink.events != []


def test_a_refused_readied_run_sends_its_set_aside_once_then_raises(tmp_path: Path) -> None:
    ready = ready_run(tmp_path, with_broken_settings(tmp_path))

    with pytest.raises(RefusedError):
        ready.start("no-such-story")

    assert [event.event for event in ready.speaker.events] == [SET_ASIDE]


def test_a_readied_run_cancelled_before_its_settings_stage_sends_its_set_aside_once(
    tmp_path: Path,
) -> None:
    ready = ready_run(tmp_path, with_broken_settings(tmp_path), FakeCancelToken(cancel_at=1))

    outcome = ready.start(STORY)

    assert outcome.cancelled
    assert [event.event for event in ready.speaker.events].count(SET_ASIDE) == 1
