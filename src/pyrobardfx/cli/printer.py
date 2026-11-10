"""The CLI printer: the one place that writes user-facing text to the terminal."""

import typer

from pyrobardfx.cli.constants import (
    REFUSAL_TEXT,
    RUN_CANCELLED_TEXT,
    RUN_FINISHED_TEXT,
    RUN_PROGRESS_FIELD_TEXT,
    RUN_PROGRESS_TEXT,
    WORKING_DIR_OPTION,
)
from pyrobardfx.events.event import PipelineEvent
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.workdir.constants import HOME_OVERRIDE_ENV
from pyrobardfx.workdir.run_folders import RunFolder


class CliPrinter:
    """Turns service outcomes into terminal text; as the CLI's event sink, prints each event."""

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

    @staticmethod
    def run_cancelled(folder: RunFolder) -> None:
        typer.echo(RUN_CANCELLED_TEXT.format(run_id=folder.run_id, path=folder.path))

    def send(self, event: PipelineEvent) -> None:
        """Write one progress line per event to stderr, apart from the text a command prints."""
        fields = "".join(
            RUN_PROGRESS_FIELD_TEXT.format(key=key, value=value)
            for key, value in event.fields.items()
        )
        text = RUN_PROGRESS_TEXT.format(
            stage=event.stage, percent=event.percent, event=event.event, fields=fields
        )
        typer.echo(text, err=True)
