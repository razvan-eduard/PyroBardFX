from pathlib import Path

from typer.testing import CliRunner

from pyrobardfx.locales.constants import Language
from pyrobardfx.locales.labels import Labels
from pyrobardfx.settings.model import Settings
from tests.builders.cli_app import CliAppBuilder
from tests.builders.locales import LocalesBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder
from tests.fakes.events import RecordingSink

STORY = "the-lighthouse"


def romanian(sandbox: Path, texts: dict[str, str]) -> Labels:
    """Labels in ro holding only `texts`, over a copy of the real en locale as their fallback."""
    return Labels.load(Language.RO, with_romanian(sandbox, texts))


def with_romanian(sandbox: Path, texts: dict[str, str]) -> Path:
    """A locales folder: a copy of the real en locale, and ro holding only `texts`."""
    return LocalesBuilder(sandbox / "locales").real(Language.EN).texts(Language.RO, texts).build()


def speaking_romanian(sandbox: Path) -> Path:
    """A working directory whose settings speak ro, with the Story `STORY` in it."""
    working = WorkingDirectoryBuilder(sandbox / "work").story(STORY)
    return working.settings(Settings(ui_language=Language.RO)).build()


def test_a_finished_run_prints_its_line_in_the_ui_language_of_the_working_directory(
    tmp_path: Path,
) -> None:
    folder = with_romanian(tmp_path, {"run.finished": "Rularea {run_id} s-a terminat: {path}"})
    app = CliAppBuilder(tmp_path).labels(Labels.load(Language.EN, folder)).build()

    result = CliRunner().invoke(
        app, ["--working-dir", str(speaking_romanian(tmp_path)), "run", STORY]
    )

    assert "s-a terminat" in result.stdout


def test_a_refused_run_prints_its_refusal_in_the_ui_language_of_the_working_directory(
    tmp_path: Path,
) -> None:
    folder = with_romanian(tmp_path, {"run.refused.no_story": "Rulare refuzată: {detail} {path}"})
    app = CliAppBuilder(tmp_path).labels(Labels.load(Language.EN, folder)).build()

    result = CliRunner().invoke(
        app, ["--working-dir", str(speaking_romanian(tmp_path)), "run", "no-such-story"]
    )

    assert "Rulare refuzată" in result.stderr


def test_a_run_prints_its_progress_lines_in_the_ui_language_of_the_working_directory(
    tmp_path: Path,
) -> None:
    folder = with_romanian(
        tmp_path, {"run.progress": "etapa {stage} {percent:.0f}% {event}{fields}"}
    )
    app = CliAppBuilder(tmp_path).labels(Labels.load(Language.EN, folder)).build()

    result = CliRunner().invoke(
        app, ["--working-dir", str(speaking_romanian(tmp_path)), "run", STORY]
    )

    assert "etapa export_per_video 100% stage_finished" in result.stderr


def test_a_refused_working_directory_prints_its_refusal_in_the_language_of_the_app(
    tmp_path: Path,
) -> None:
    labels = romanian(
        tmp_path, {"workdir.refused.in_temp": "Refuzat {path} {detail} {option} {env}"}
    )
    app = CliAppBuilder(tmp_path).labels(labels).build()

    result = CliRunner().invoke(
        app, ["--working-dir", str(tmp_path / "system-temp" / "work"), "run", STORY]
    )

    assert "Refuzat" in result.stderr


def test_the_help_of_a_command_is_english_whatever_the_language_of_the_app(
    tmp_path: Path,
) -> None:
    labels = romanian(tmp_path, {"cli.run.help": "Ajutor"})
    app = CliAppBuilder(tmp_path).labels(labels).build()

    result = CliRunner().invoke(app, ["run", "--help"])

    assert "Ajutor" not in result.stdout


class _Ran:
    """What a Run left behind in one language: its event names and the files it wrote."""

    def __init__(self, sandbox: Path, settings: Settings) -> None:
        root = WorkingDirectoryBuilder(sandbox / "work").story(STORY).settings(settings).build()
        sink = RecordingSink()
        app = CliAppBuilder(sandbox).sink(sink).build()
        CliRunner().invoke(app, ["--working-dir", str(root), "run", STORY])
        self.events = [(event.stage, event.event, tuple(event.fields)) for event in sink.events]
        self.files = sorted(path.relative_to(root) for path in root.rglob("*"))


def test_changing_both_languages_changes_no_event_name_run_folder_or_file_name(
    tmp_path: Path,
) -> None:
    english = _Ran(tmp_path / "en", Settings())
    romanian = _Ran(tmp_path / "ro", Settings(ui_language=Language.RO, story_language=Language.RO))

    assert (romanian.events, romanian.files) == (english.events, english.files)


def test_a_failing_sink_is_reported_on_the_command_stderr_in_the_ui_language(
    tmp_path: Path,
) -> None:
    folder = with_romanian(tmp_path, {"events.sink_failed": "Destinația {sink} a cedat: {reason}"})
    app = (
        CliAppBuilder(tmp_path)
        .labels(Labels.load(Language.EN, folder))
        .sink(RecordingSink(OSError("disk full")))
        .build()
    )

    result = CliRunner().invoke(
        app, ["--working-dir", str(speaking_romanian(tmp_path)), "run", STORY]
    )

    assert result.stderr.count("Destinația RecordingSink a cedat: disk full") == 1
