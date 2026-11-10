"""The pipeline event: one structured record of the Run's event stream."""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from pyrobardfx.events.constants import NOT_UTC_MESSAGE, PERCENT_DONE, PERCENT_START, UTC_OFFSET
from pyrobardfx.store.constants import EXTRA_FORBID

type EventValue = str | int | float | bool


class PipelineEvent(BaseModel):
    """What happened, in which stage, how far the stage got, when, plus the event's own fields."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    event: str
    stage: str
    percent: float = Field(ge=PERCENT_START, le=PERCENT_DONE)
    timestamp: AwareDatetime
    fields: dict[str, EventValue] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def _in_utc(cls, timestamp: AwareDatetime) -> AwareDatetime:
        """Refuse a timestamp in any zone but UTC, so every sink's times sort and compare."""
        offset = timestamp.utcoffset()
        if offset != UTC_OFFSET:
            raise ValueError(NOT_UTC_MESSAGE.format(offset=offset))
        return timestamp
