"""The `pyrobardfx` typer app and its console-script entry point."""

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

import typer

from pyrobardfx.cli.constants import (
    APP_NAME,
    CANCELLED_EXIT_CODE,
    NO_WORKING_DIRECTORY_MESSAGE,
    REFUSED_EXIT_CODE,
    RUN_COMMAND,
    RUN_HELP_KEY,
    STORY_HELP_KEY,
    WORKING_DIR_HELP_KEY,
    WORKING_DIR_OPTION,
)
from pyrobardfx.cli.printer import CliPrinter
from pyrobardfx.clock.base import Clock
from pyrobardfx.clock.system import SystemClock
from pyrobardfx.events.fan_out import EventFanOut, EventSink
from pyrobardfx.locales.constants import FALLBACK_LANGUAGE, Language
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.cancel import CancelFlag, CancelToken
from pyrobardfx.run.constants import SETTINGS_STAGE
from pyrobardfx.run.service import RunService
from pyrobardfx.run.settings_stage import SettingsStage
from pyrobardfx.run.tokens import SecretsTokenSource, TokenSource
from pyrobardfx.settings.service import SettingsService
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
        cancel: CancelToken,
        labels: Labels,
        sinks: Sequence[EventSink] = (),
    ) -> typer.Typer:
        """Build the app over the given adapters; each event goes to the CLI printer and `sinks`.

        Until the settings are open the printer speaks the language of `labels`; a command that
        opens them speaks their `ui_language`, read from the locales folder of `labels`. The help
        is en, as it resolves here, before `--working-dir` says where the settings are.
        """
        app = typer.Typer(name=APP_NAME, add_completion=False)
        help_text = labels.for_language(FALLBACK_LANGUAGE)
        printer = CliPrinter(labels)
        events = EventFanOut(clock, (printer, *sinks), labels=labels)
        service = WorkingDirectoryService(host, events)

        @app.callback(invoke_without_command=True)
        def start(
            ctx: typer.Context,
            working_dir: Annotated[
                Path | None,
                typer.Option(WORKING_DIR_OPTION, help=help_text.label(WORKING_DIR_HELP_KEY)),
            ] = None,
        ) -> None:
            try:
                ctx.obj = service.open(working_dir)
            except RefusedError as error:
                printer.refused(error)
                raise typer.Exit(code=REFUSED_EXIT_CODE) from error

        @app.command(RUN_COMMAND, help=help_text.label(RUN_HELP_KEY))
        def run(
            ctx: typer.Context,
            story: Annotated[str, typer.Argument(help=help_text.label(STORY_HELP_KEY))],
        ) -> None:
            working = ctx.find_object(WorkingDirectory)
            if working is None:
                raise RuntimeError(NO_WORKING_DIRECTORY_MESSAGE)
            # The settings stage replays each set-aside event into the Run, which also logs it to
            # `run.log`; opening on a fan-out without sinks makes a replay the only send.
            settings = SettingsService.open(working, clock, EventFanOut(clock, ()))
            # From here on the lines speak the UI language of the opened settings.
            speaking = labels.for_language(settings.read().ui_language)
            run_printer = CliPrinter(speaking)
            run_events = EventFanOut(clock, (run_printer, *sinks), labels=speaking)
            runs = RunService(working, clock, tokens, trash, run_events, cancel, settings)
            # A Run that ends before its settings stage leaves set-aside records unsent; send them.
            unsent = run_events.at(SETTINGS_STAGE)
            try:
                outcome = runs.start(story)
            except RefusedError as error:
                SettingsStage.replay(settings, unsent)
                run_printer.refused(error)
                raise typer.Exit(code=REFUSED_EXIT_CODE) from error
            if outcome.cancelled:
                SettingsStage.replay(settings, unsent)
                run_printer.run_cancelled(outcome.folder)
                raise typer.Exit(code=CANCELLED_EXIT_CODE)
            run_printer.run_finished(outcome.folder)

        return app


def main() -> None:
    clock = SystemClock()
    host = HostFacts.from_host()
    labels = Labels.load(Language.EN)
    CliApp.build(host, clock, SecretsTokenSource(), Send2TrashTrash(clock), CancelFlag(), labels)()
