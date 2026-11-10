"""Builds the CLI app over fakes only, so no test reaches the system clock, random or trash."""

from pathlib import Path
from typing import Self

import typer

from pyrobardfx.cli.app import CliApp
from pyrobardfx.workdir.host import HostFacts
from tests.builders.host_facts import HostFactsBuilder
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.clock import START, FakeClock
from tests.fakes.events import RecordingSink
from tests.fakes.tokens import FixedTokenSource
from tests.fakes.trash import FakeTrash


class CliAppBuilder:
    """Fluent builder of the CLI app; every adapter defaults to its fake, inside `sandbox`."""

    def __init__(self, sandbox: Path) -> None:
        self._sandbox = sandbox
        self._host: HostFacts | None = None
        self._clock: FakeClock | None = None
        self._tokens = FixedTokenSource("a1b2")
        self._trash: FakeTrash | None = None
        self._cancel = FakeCancelToken()
        self._sinks: list[RecordingSink] = []

    def host(self, host: HostFacts) -> Self:
        self._host = host
        return self

    def clock(self, clock: FakeClock) -> Self:
        self._clock = clock
        return self

    def tokens(self, tokens: FixedTokenSource) -> Self:
        self._tokens = tokens
        return self

    def trash(self, trash: FakeTrash) -> Self:
        self._trash = trash
        return self

    def cancel(self, cancel: FakeCancelToken) -> Self:
        self._cancel = cancel
        return self

    def sink(self, sink: RecordingSink) -> Self:
        """Send every event of the app to `sink` too, beside the CLI printer."""
        self._sinks.append(sink)
        return self

    def build(self) -> typer.Typer:
        clock = self._clock or FakeClock(START)
        return CliApp.build(
            self._host or HostFactsBuilder(self._sandbox).build(),
            clock,
            self._tokens,
            self._trash or FakeTrash(clock, self._sandbox / "trash"),
            self._cancel,
            self._sinks,
        )
