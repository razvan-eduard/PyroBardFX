"""Event sinks that write the event stream to a file."""

from typing import TextIO

from pyrobardfx.events.constants import LINE_END
from pyrobardfx.events.event import PipelineEvent


class JsonLinesSink:
    """Writes each event as one JSON line to an open text file, for example the Run's `run.log`."""

    def __init__(self, handle: TextIO) -> None:
        self._handle = handle

    def send(self, event: PipelineEvent) -> None:
        self._handle.write(event.model_dump_json() + LINE_END)
