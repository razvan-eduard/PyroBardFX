"""The fake event sink: keeps every event it is sent, so a test can read them back."""

from pyrobardfx.events.event import PipelineEvent


class RecordingSink:
    """An event sink that keeps the events it is sent, in order, in `events`.

    Given `fails_with`, it keeps each event and then raises that error, as a broken sink would.
    """

    def __init__(self, fails_with: Exception | None = None) -> None:
        self.events: list[PipelineEvent] = []
        self._fails_with = fails_with

    def send(self, event: PipelineEvent) -> None:
        self.events.append(event)
        if self._fails_with is not None:
            raise self._fails_with
