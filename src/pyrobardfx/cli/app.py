"""The `pyrobardfx` typer app and its console-script entry point."""

import sys
from pathlib import Path
from typing import Annotated

import structlog
import typer

from pyrobardfx.cli.constants import (
    APP_NAME,
    REFUSED_EXIT_CODE,
    WORKING_DIR_HELP,
    WORKING_DIR_OPTION,
)
from pyrobardfx.cli.printer import CliPrinter
from pyrobardfx.workdir.host import HostFacts
from pyrobardfx.workdir.working_directory import (
    WorkingDirectoryRefusedError,
    WorkingDirectoryService,
)


class CliApp:
    """Builds the typer app over the services for one host."""

    @staticmethod
    def build(host: HostFacts) -> typer.Typer:
        app = typer.Typer(name=APP_NAME, add_completion=False)
        service = WorkingDirectoryService(host)

        @app.callback(invoke_without_command=True)
        def start(
            working_dir: Annotated[
                Path | None, typer.Option(WORKING_DIR_OPTION, help=WORKING_DIR_HELP)
            ] = None,
        ) -> None:
            try:
                service.open(working_dir)
            except WorkingDirectoryRefusedError as error:
                CliPrinter.refused(error)
                raise typer.Exit(code=REFUSED_EXIT_CODE) from error

        return app

    @staticmethod
    def configure_logging() -> None:
        """Send log events to stderr so they never mix with the text a command prints."""
        structlog.configure(logger_factory=structlog.PrintLoggerFactory(sys.stderr))


def main() -> None:
    CliApp.configure_logging()
    CliApp.build(HostFacts.from_host())()
