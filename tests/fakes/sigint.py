"""The fake SIGINT handler: stands in for the process handler a Run must give back."""

from types import FrameType


class RecordingSigintHandler:
    """A SIGINT handler that counts the signals it is called with, in `calls`."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, signum: int, frame: FrameType | None) -> None:
        self.calls += 1
