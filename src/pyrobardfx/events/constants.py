"""Constants every progress event shares."""

from datetime import timedelta

PERCENT_START = 0.0
PERCENT_DONE = 100.0
LINE_END = "\n"
UTC_OFFSET = timedelta(0)
NOT_UTC_MESSAGE = "an event timestamp must be in UTC, got offset {offset}"

# The key under which the processor chain hands the checked event on to the sinks.
EVENT_RECORD_KEY = "record"
# English text of the key `events.sink_failed`, until `label(key)` and the locales take it.
EVENTS_SINK_FAILED_TEXT = "Event sink {sink} failed and gets no further events: {reason}"
