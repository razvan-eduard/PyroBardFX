"""Constants every progress event shares."""

from datetime import timedelta

PERCENT_START = 0.0
PERCENT_DONE = 100.0
UTC_OFFSET = timedelta(0)
NOT_UTC_MESSAGE = "an event timestamp must be in UTC, got offset {offset}"

# The key under which the processor chain hands the checked event on to the sinks.
EVENT_RECORD_KEY = "record"
# The key under which the processor chain stamps the clock's UTC time on an event.
TIMESTAMP_FIELD = "timestamp"
# The locale key of the line that reports a failed sink.
EVENTS_SINK_FAILED_LABEL_KEY = "events.sink_failed"
