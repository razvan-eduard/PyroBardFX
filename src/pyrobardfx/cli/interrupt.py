"""SIGINT during a Run: the CLI's end of the cancel token."""

import signal
from collections.abc import Callable
from types import FrameType, TracebackType
from typing import Self

from pyrobardfx.run.cancel import CancellableToken

type SigintHandler = Callable[[int, FrameType | None], object] | int | signal.Handlers


class SigintCancel:
    """For the span of a `with` block, SIGINT cancels `token` instead of interrupting the app.

    On leaving the block, success or failure, the handler from before the block is back, so a
    SIGINT outside a Run behaves as it did. Enter it from the main thread only, as `signal` asks.
    """

    def __init__(self, token: CancellableToken) -> None:
        self._token = token
        self._previous: SigintHandler = signal.SIG_DFL

    def __enter__(self) -> Self:
        previous = signal.signal(signal.SIGINT, self._cancel)
        # `None` means a handler not set from Python; the default one is the nearest stand-in.
        self._previous = signal.SIG_DFL if previous is None else previous
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        signal.signal(signal.SIGINT, self._previous)

    def _cancel(self, signum: int, frame: FrameType | None) -> None:
        self._token.cancel()
