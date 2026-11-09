"""The CLI printer: the one place that writes user-facing text to the terminal."""

import typer

from pyrobardfx.cli.constants import REFUSAL_TEXT, WORKING_DIR_OPTION
from pyrobardfx.workdir.constants import HOME_OVERRIDE_ENV
from pyrobardfx.workdir.working_directory import WorkingDirectoryRefusedError


class CliPrinter:
    """Turns service outcomes into terminal text."""

    @staticmethod
    def refused(error: WorkingDirectoryRefusedError) -> None:
        text = REFUSAL_TEXT[error.reason].format(
            path=error.path,
            detail=error.detail,
            option=WORKING_DIR_OPTION,
            env=HOME_OVERRIDE_ENV,
        )
        typer.echo(text, err=True)
