"""The fake event sink: keeps every event it is sent, so a test can read them back."""

from collections.abc import Callable

from pyrobardfx.events.event import PipelineEvent


class RecordingSink:
    """An event sink that keeps the events it is sent, in order, in `events`.

    Given `fails_with`, it keeps each event and then raises that error, as a broken sink would.
    Given `on_event`, it calls it with each event it keeps, as a listener acting mid-Run would.
    """

    def __init__(
        self,
        fails_with: Exception | None = None,
        on_event: Callable[[PipelineEvent], None] | None = None,
    ) -> None:
        self.events: list[PipelineEvent] = []
        self._fails_with = fails_with
        self._on_event = on_event

    def send(self, event: PipelineEvent) -> None:
        self.events.append(event)
        if self._on_event is not None:
            self._on_event(event)
        if self._fails_with is not None:
            raise self._fails_with
