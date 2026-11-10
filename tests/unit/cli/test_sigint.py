import json
import signal
from pathlib import Path

from typer.testing import CliRunner, Result

from pyrobardfx.events.event import PipelineEvent
from tests.builders.cli_app import CliAppBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder
from tests.fakes.events import RecordingSink
from tests.fakes.sigint import RecordingSigintHandler

STORY = "the-lighthouse"
RUN_ID = "20261109T153000Z-a1b2"


def interrupt(event: PipelineEvent) -> None:
    """Send SIGINT once the first stage passed its cancel check, as a Ctrl-C mid-Run would."""
    if event.event == "stage_started" and event.stage == "prune_runs":
        signal.raise_signal(signal.SIGINT)


def run_story(sandbox: Path, story: str = STORY, sink: RecordingSink | None = None) -> Result:
    root = WorkingDirectoryBuilder(sandbox / "work").story(STORY).build()
    app = CliAppBuilder(sandbox).sink(sink or RecordingSink()).build()
    return CliRunner().invoke(app, ["--working-dir", str(root), "run", story])


def test_sigint_during_a_run_stops_it_with_its_cancelled_line_and_code(
    tmp_path: Path, previous_sigint: RecordingSigintHandler
) -> None:
    result = run_story(tmp_path, sink=RecordingSink(on_event=interrupt))

    assert (result.exit_code, f"Run {RUN_ID} cancelled" in result.stdout) == (130, True)
    assert previous_sigint.calls == 0


def test_sigint_during_a_run_stops_it_at_its_next_cancel_check(
    tmp_path: Path, previous_sigint: RecordingSigintHandler
) -> None:
    run_story(tmp_path, sink=RecordingSink(on_event=interrupt))

    log = tmp_path / "work" / "stories" / STORY / "runs" / RUN_ID / "run.log"
    events = [json.loads(line) for line in log.read_text().splitlines()]
    assert [event["stage"] for event in events if event["event"] == "run_cancelled"] == [
        "working_directory_open"
    ]


def test_a_finished_run_gives_back_the_sigint_handler_from_before_it(
    tmp_path: Path, previous_sigint: RecordingSigintHandler
) -> None:
    result = run_story(tmp_path)

    assert (result.exit_code, signal.getsignal(signal.SIGINT)) == (0, previous_sigint)


def test_a_refused_run_gives_back_the_sigint_handler_from_before_it(
    tmp_path: Path, previous_sigint: RecordingSigintHandler
) -> None:
    result = run_story(tmp_path, story="no-such-story")

    assert (result.exit_code, signal.getsignal(signal.SIGINT)) == (1, previous_sigint)
