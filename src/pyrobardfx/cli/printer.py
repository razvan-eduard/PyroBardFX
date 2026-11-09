"""The CLI printer: the one place that writes user-facing text to the terminal."""

import typer

from pyrobardfx.cli.constants import (
    REFUSAL_TEXT,
    RUN_FINISHED_TEXT,
    WORKING_DIR_OPTION,
)
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.workdir.constants import HOME_OVERRIDE_ENV
from pyrobardfx.workdir.run_folders import RunFolder


class CliPrinter:
    """Turns service outcomes into terminal text."""

    @staticmethod
    def refused(error: RefusedError) -> None:
        text = REFUSAL_TEXT[error.reason].format(
            path=error.path,
            detail=error.detail,
            option=WORKING_DIR_OPTION,
            env=HOME_OVERRIDE_ENV,
        )
        typer.echo(text, err=True)

    @staticmethod
    def run_finished(folder: RunFolder) -> None:
        typer.echo(RUN_FINISHED_TEXT.format(run_id=folder.run_id, path=folder.path))
