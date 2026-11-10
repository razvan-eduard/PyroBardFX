"""The settings stamp: the settings a script records, short because it holds non-defaults only."""

from typing import Self

from pydantic import BaseModel, ConfigDict, JsonValue

from pyrobardfx.settings.model import Settings
from pyrobardfx.store.constants import DUMP_MODE, EXTRA_FORBID


class SettingsStamp(BaseModel):
    """The fields of some settings that differ from the defaults, as JSON values by name."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    values: dict[str, JsonValue]

    @classmethod
    def of(cls, settings: Settings) -> Self:
        return cls(values=settings.model_dump(mode=DUMP_MODE, exclude_defaults=True))
