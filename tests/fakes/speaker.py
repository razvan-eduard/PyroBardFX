"""The fake Run speaker: keeps what a Run says to it, so a test can read it back."""

from pyrobardfx.events.event import PipelineEvent
from pyrobardfx.locales.labels import Labels


class RecordingSpeaker:
    """A Run speaker in the language of `labels`; keeps each event in `events` and each text
    the fan-out reports a failed sink with in `written`."""

    def __init__(self, labels: Labels) -> None:
        self.labels = labels
        self.events: list[PipelineEvent] = []
        self.written: list[str] = []

    def send(self, event: PipelineEvent) -> None:
        self.events.append(event)

    def write(self, text: str, /) -> None:
        self.written.append(text)
