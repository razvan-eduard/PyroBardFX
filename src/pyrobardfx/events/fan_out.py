"""The event fan-out: a structlog logger whose processor chain ends in the event sinks."""

from collections.abc import Sequence
from typing import Protocol, Self

import structlog
from structlog.typing import EventDict, WrappedLogger

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import EVENT_RECORD_KEY, EVENTS_SINK_FAILED_KEY, TIMESTAMP_FIELD
from pyrobardfx.events.event import EventValue, PipelineEvent
from pyrobardfx.locales.labels import Labels
from pyrobardfx.store.constants import LINE_END


class EventSink(Protocol):
    """Takes every event of the stream, for example the `run.log` file or the CLI printer."""

    def send(self, event: PipelineEvent) -> None:
        """Take one event."""
        ...


class ErrorStream(Protocol):
    """Where a failed sink is reported: a text file such as `io.StringIO`, or the CLI printer."""

    def write(self, text: str, /) -> object:
        """Write `text` as it is, line end included."""
        ...


class _IsolatedSink:
    """One sink at the end of the processor chain; once it raises, it is reported and skipped."""

    def __init__(self, sink: EventSink, errors: ErrorStream, labels: Labels) -> None:
        self._sink = sink
        self._errors = errors
        self._labels = labels
        self._failed = False

    # structlog types the wrapped logger and the event dict with `Any` values.
    def __call__(self, logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
        if self._failed:
            return event_dict
        try:
            self._sink.send(event_dict[EVENT_RECORD_KEY])
        except Exception as error:  # Any sink failure must leave the Run going.
            self._failed = True
            text = self._labels.label(EVENTS_SINK_FAILED_KEY).format(
                sink=type(self._sink).__name__, reason=error
            )
            self._errors.write(text + LINE_END)
        return event_dict


class EventFanOut:
    """Sends each event to every sink it holds; adding a sink touches no code that emits.

    The events travel through a structlog logger: its processor chain stamps the clock's UTC
    time, checks the event and ends in the sinks. A sink that raises is reported once on
    `errors`, in the language of `labels`, and gets no further events; the other sinks go on.
    The caller picks both: the CLI passes its error stream and the labels it speaks.
    """

    def __init__(
        self,
        clock: Clock,
        sinks: Sequence[EventSink],
        errors: ErrorStream,
        labels: Labels,
    ) -> None:
        self._clock = clock
        self._errors = errors
        self._labels = labels
        self._sinks = tuple(_IsolatedSink(sink, errors, labels) for sink in sinks)

    def with_sink(self, sink: EventSink) -> Self:
        """Return a fan-out that also sends to `sink`; this one keeps its own sinks."""
        wider = type(self)(self._clock, (), self._errors, self._labels)
        wider._sinks = (*self._sinks, _IsolatedSink(sink, self._errors, self._labels))
        return wider

    def at(self, stage: str) -> StageEvents:
        """Return the emitter of the events of `stage`."""
        processors = (self._stamp, self._check, *self._sinks, self._drop)
        logger: structlog.BoundLogger = structlog.wrap_logger(
            structlog.ReturnLogger(), processors=processors, wrapper_class=structlog.BoundLogger
        )
        return StageEvents(logger.bind(stage=stage))

    # structlog types the wrapped logger and the event dict with `Any` values.
    def _stamp(self, logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
        event_dict[TIMESTAMP_FIELD] = self._clock.utc_now()
        return event_dict

    # structlog types the wrapped logger and the event dict with `Any` values.
    @staticmethod
    def _check(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
        """Turn the event dict into a checked event; a bad event raises before any sink."""
        return {EVENT_RECORD_KEY: PipelineEvent.model_validate(event_dict)}

    # structlog types the wrapped logger and the event dict with `Any` values.
    @staticmethod
    def _drop(logger: WrappedLogger, method: str, event_dict: EventDict) -> EventDict:
        """End the chain: every sink has the event, so the wrapped logger gets nothing."""
        raise structlog.DropEvent


class StageEvents:
    """Emits the events of one stage through its bound logger; the emitter never names its stage."""

    def __init__(self, logger: structlog.BoundLogger) -> None:
        self._logger = logger

    def emit(self, event: str, percent: float, **fields: EventValue) -> None:
        self._logger.info(event, percent=percent, fields=fields)
