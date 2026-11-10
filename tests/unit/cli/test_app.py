from pathlib import Path

from typer.testing import CliRunner

from pyrobardfx.locales.constants import Language
from pyrobardfx.locales.labels import Labels
from tests.builders.cli_app import CliAppBuilder
from tests.builders.locales import LocalesBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder

STORY = "the-lighthouse"


def romanian(sandbox: Path, texts: dict[str, str]) -> Labels:
    """Labels in ro holding only `texts`, over a copy of the real en locale as their fallback."""
    folder = LocalesBuilder(sandbox / "locales").real(Language.EN).texts(Language.RO, texts)
    return Labels.load(Language.RO, folder.build())


def test_a_finished_run_prints_its_line_in_the_language_of_the_app(tmp_path: Path) -> None:
    labels = romanian(tmp_path, {"run.finished": "Rularea {run_id} s-a terminat: {path}"})
    root = WorkingDirectoryBuilder(tmp_path / "work").story(STORY).build()
    app = CliAppBuilder(tmp_path).labels(labels).build()

    result = CliRunner().invoke(app, ["--working-dir", str(root), "run", STORY])

    assert "s-a terminat" in result.stdout


def test_the_help_of_a_command_is_english_whatever_the_language_of_the_app(
    tmp_path: Path,
) -> None:
    labels = romanian(tmp_path, {"cli.run.help": "Ajutor"})
    app = CliAppBuilder(tmp_path).labels(labels).build()

    result = CliRunner().invoke(app, ["run", "--help"])

    assert "Ajutor" not in result.stdout
