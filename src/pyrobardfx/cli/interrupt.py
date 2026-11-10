"""SIGINT during a Run: the CLI's end of the cancel token."""

import signal
from collections.abc import Callable
from types import FrameType, TracebackType
from typing import Self

from pyrobardfx.run.cancel import CancellableToken

type SigintHandler = Callable[[int, FrameType | None], object] | int | signal.Handlers


class SigintCancel:
    """For the span of a `with` block, the first SIGINT cancels `token` instead of a hard stop.

    Every later SIGINT in the same span goes to the handler from before the block, a hard stop;
    under Python's default handler that is a `KeyboardInterrupt`. Each span counts afresh. On
    leaving the block, success or failure, the handler from before the block is back, so a SIGINT
    outside a Run behaves as it did. Enter it from the main thread only, as `signal` asks.
    """

    def __init__(self, token: CancellableToken) -> None:
        self._token = token
        self._previous: SigintHandler = signal.SIG_DFL
        self._interrupted = False

    def __enter__(self) -> Self:
        self._interrupted = False
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
        if not self._interrupted:
            self._interrupted = True
            self._token.cancel()
        elif callable(self._previous):
            self._previous(signum, frame)
        else:
            # `SIG_IGN` and `SIG_DFL` cannot be called; put the one back and let it take the signal.
            signal.signal(signal.SIGINT, self._previous)
            signal.raise_signal(signal.SIGINT)
