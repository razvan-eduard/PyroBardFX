"""The `pyrobardfx` typer app and its console-script entry point."""

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

import typer

from pyrobardfx.adapters.constants import DeviceChoice
from pyrobardfx.adapters.devices import DeviceProbe, SystemDeviceProbe
from pyrobardfx.cli.constants import (
    APP_NAME,
    CANCELLED_EXIT_CODE,
    DEVICE_HELP_LABEL_KEY,
    DEVICE_META_KEY,
    DEVICE_OPTION,
    NO_WORKING_DIRECTORY_MESSAGE,
    REFUSED_EXIT_CODE,
    RUN_COMMAND,
    RUN_HELP_LABEL_KEY,
    STORY_HELP_LABEL_KEY,
    WORKING_DIR_HELP_LABEL_KEY,
    WORKING_DIR_OPTION,
)
from pyrobardfx.cli.interrupt import SigintCancel
from pyrobardfx.cli.printer import CliPrinter
from pyrobardfx.clock.base import Clock
from pyrobardfx.clock.system import SystemClock
from pyrobardfx.domain.tokens import SecretsTokenSource, TokenSource
from pyrobardfx.events.fan_out import EventFanOut, EventSink
from pyrobardfx.locales.constants import FALLBACK_LANGUAGE, Language
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.cancel import CancellableToken, ThreadCancelToken
from pyrobardfx.run.factory import RunFactory
from pyrobardfx.trash.base import Trash
from pyrobardfx.trash.system import Send2TrashTrash
from pyrobardfx.workdir.host import HostFacts
from pyrobardfx.workdir.working_directory import WorkingDirectory, WorkingDirectoryService


class CliApp:
    """Builds the typer app over the services for one host."""

    @staticmethod
    def build(
        host: HostFacts,
        clock: Clock,
        tokens: TokenSource,
        trash: Trash,
        cancel: CancellableToken,
        labels: Labels,
        devices: DeviceProbe,
        sinks: Sequence[EventSink] = (),
    ) -> typer.Typer:
        """Build the app over the given adapters; each event goes to the CLI printer and `sinks`.

        Until the settings are open the printer speaks the language of `labels`; a command that
        opens them speaks their `ui_language`, read from the locales folder of `labels`. The help
        is en, as it resolves here, before `--working-dir` says where the settings are.

        `--device` is left in the context's meta under `DEVICE_META_KEY`; the `run` command hands
        it to the device resolver, where it wins over the device setting. `devices` tells the
        resolver which backends the machine offers.
        """
        app = typer.Typer(name=APP_NAME, add_completion=False)
        help_text = labels.for_language(FALLBACK_LANGUAGE)
        printer = CliPrinter(labels)
        events = EventFanOut(clock, (printer, *sinks), printer, labels)
        service = WorkingDirectoryService(host, events)

        @app.callback(invoke_without_command=True)
        def start(
            ctx: typer.Context,
            working_dir: Annotated[
                Path | None,
                typer.Option(WORKING_DIR_OPTION, help=help_text.label(WORKING_DIR_HELP_LABEL_KEY)),
            ] = None,
            device: Annotated[
                DeviceChoice,
                typer.Option(DEVICE_OPTION, help=help_text.label(DEVICE_HELP_LABEL_KEY)),
            ] = DeviceChoice.AUTO,
        ) -> None:
            ctx.meta[DEVICE_META_KEY] = device
            try:
                ctx.obj = service.open(working_dir)
            except RefusedError as error:
                printer.refused(error)
                raise typer.Exit(code=REFUSED_EXIT_CODE) from error

        runs = RunFactory(clock, tokens, trash, cancel, labels, devices, sinks)
        CliApp._add_run(app, help_text, runs, cancel)
        return app

    @staticmethod
    def _add_run(
        app: typer.Typer, help_text: Labels, runs: RunFactory, cancel: CancellableToken
    ) -> None:
        """Register the `run` command, which speaks the `ui_language` of the opened settings.

        For the span of the Run, the first SIGINT cancels `cancel`; the Run stops at its next cancel
        check. A second SIGINT goes to the handler from before the Run and stops the app hard.
        """

        @app.command(RUN_COMMAND, help=help_text.label(RUN_HELP_LABEL_KEY))
        def run(
            ctx: typer.Context,
            story: Annotated[str, typer.Argument(help=help_text.label(STORY_HELP_LABEL_KEY))],
        ) -> None:
            working = ctx.find_object(WorkingDirectory)
            if working is None:
                raise RuntimeError(NO_WORKING_DIRECTORY_MESSAGE)
            ready = runs.open(working, CliPrinter, ctx.meta[DEVICE_META_KEY])
            try:
                with SigintCancel(cancel):
                    outcome = ready.start(story)
            except RefusedError as error:
                ready.speaker.refused(error)
                raise typer.Exit(code=REFUSED_EXIT_CODE) from error
            if outcome.cancelled:
                ready.speaker.run_cancelled(outcome.folder)
                raise typer.Exit(code=CANCELLED_EXIT_CODE)
            ready.speaker.run_finished(outcome.folder)


def main() -> None:
    clock = SystemClock()
    host = HostFacts.from_host()
    labels = Labels.load(Language.EN)
    CliApp.build(
        host,
        clock,
        SecretsTokenSource(),
        Send2TrashTrash(clock),
        ThreadCancelToken(),
        labels,
        SystemDeviceProbe(),
    )()
