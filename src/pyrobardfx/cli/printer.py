"""The CLI printer: the one place that writes user-facing text to the terminal."""

import typer

from pyrobardfx.cli.constants import (
    RUN_CANCELLED_LABEL_KEY,
    RUN_FINISHED_LABEL_KEY,
    RUN_PROGRESS_FIELD_LABEL_KEY,
    RUN_PROGRESS_LABEL_KEY,
    WORKING_DIR_OPTION,
)
from pyrobardfx.events.event import PipelineEvent
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.constants import DETAIL_FIELD, ENV_FIELD, OPTION_FIELD, PATH_FIELD
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.workdir.constants import HOME_OVERRIDE_ENV
from pyrobardfx.workdir.run_folders import RunFolder


class CliPrinter:
    """Turns service outcomes into terminal text in the language of `labels`; as the CLI's event
    sink, prints each event. Ids, stage and event names go out as they are, never translated."""

    def __init__(self, labels: Labels) -> None:
        self._labels = labels

    def refused(self, error: RefusedError) -> None:
        labelled = {name: self._labels.label(key) for name, key in error.labelled.items()}
        fixed = {
            PATH_FIELD: error.path,
            DETAIL_FIELD: error.detail,
            OPTION_FIELD: WORKING_DIR_OPTION,
            ENV_FIELD: HOME_OVERRIDE_ENV,
        }
        text = self._labels.label(error.reason).format(**fixed, **error.literal, **labelled)
        typer.echo(text, err=True)

    def write(self, text: str) -> None:
        """Write `text` to stderr as it is: the fan-out reports a failed event sink here."""
        typer.echo(text, err=True, nl=False)

    def run_finished(self, folder: RunFolder) -> None:
        text = self._labels.label(RUN_FINISHED_LABEL_KEY)
        typer.echo(text.format(run_id=folder.run_id, path=folder.path))

    def run_cancelled(self, folder: RunFolder) -> None:
        text = self._labels.label(RUN_CANCELLED_LABEL_KEY)
        typer.echo(text.format(run_id=folder.run_id, path=folder.path))

    def send(self, event: PipelineEvent) -> None:
        """Write one progress line per event to stderr, apart from the text a command prints."""
        field = self._labels.label(RUN_PROGRESS_FIELD_LABEL_KEY)
        fields = "".join(field.format(key=key, value=value) for key, value in event.fields.items())
        text = self._labels.label(RUN_PROGRESS_LABEL_KEY).format(
            stage=event.stage, percent=event.percent, event=event.event, fields=fields
        )
        typer.echo(text, err=True)
