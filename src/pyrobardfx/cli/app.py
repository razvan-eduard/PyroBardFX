"""The `pyrobardfx` typer app and its console-script entry point."""

import sys
from pathlib import Path
from typing import Annotated

import structlog
import typer

from pyrobardfx.cli.constants import (
    APP_NAME,
    NO_WORKING_DIRECTORY_MESSAGE,
    REFUSED_EXIT_CODE,
    RUN_COMMAND,
    RUN_HELP,
    STORY_HELP,
    WORKING_DIR_HELP,
    WORKING_DIR_OPTION,
)
from pyrobardfx.cli.printer import CliPrinter
from pyrobardfx.clock.base import Clock
from pyrobardfx.clock.system import SystemClock
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.service import RunService
from pyrobardfx.run.tokens import SecretsTokenSource, TokenSource
from pyrobardfx.trash.base import Trash
from pyrobardfx.trash.system import Send2TrashTrash
from pyrobardfx.workdir.host import HostFacts
from pyrobardfx.workdir.working_directory import WorkingDirectory, WorkingDirectoryService


class CliApp:
    """Builds the typer app over the services for one host."""

    @staticmethod
    def build(
        host: HostFacts,
        clock: Clock | None = None,
        tokens: TokenSource | None = None,
        trash: Trash | None = None,
    ) -> typer.Typer:
        """Build the app; `clock`, `tokens` and `trash` default to the system's own."""
        app = typer.Typer(name=APP_NAME, add_completion=False)
        service = WorkingDirectoryService(host)
        run_clock = clock or SystemClock()
        run_tokens = tokens or SecretsTokenSource()
        run_trash = trash or Send2TrashTrash(run_clock)

        @app.callback(invoke_without_command=True)
        def start(
            ctx: typer.Context,
            working_dir: Annotated[
                Path | None, typer.Option(WORKING_DIR_OPTION, help=WORKING_DIR_HELP)
            ] = None,
        ) -> None:
            try:
                ctx.obj = service.open(working_dir)
            except RefusedError as error:
                CliPrinter.refused(error)
                raise typer.Exit(code=REFUSED_EXIT_CODE) from error

        @app.command(RUN_COMMAND, help=RUN_HELP)
        def run(
            ctx: typer.Context,
            story: Annotated[str, typer.Argument(help=STORY_HELP)],
        ) -> None:
            working = ctx.find_object(WorkingDirectory)
            if working is None:
                raise RuntimeError(NO_WORKING_DIRECTORY_MESSAGE)
            try:
                folder = RunService(working, run_clock, run_tokens, run_trash).start(story)
            except RefusedError as error:
                CliPrinter.refused(error)
                raise typer.Exit(code=REFUSED_EXIT_CODE) from error
            CliPrinter.run_finished(folder)

        return app

    @staticmethod
    def configure_logging() -> None:
        """Send log events to stderr so they never mix with the text a command prints."""
        structlog.configure(logger_factory=structlog.PrintLoggerFactory(sys.stderr))


def main() -> None:
    CliApp.configure_logging()
    clock = SystemClock()
    CliApp.build(HostFacts.from_host(), clock, SecretsTokenSource(), Send2TrashTrash(clock))()
