"""The settings model: every setting defined once, with its keys and constraints."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonDict

from pyrobardfx.settings.constants import (
    DEFAULT_RUNS_TO_KEEP,
    GROUP_KEY,
    HELP_KEY,
    LABEL_KEY,
    MIN_RUNS_TO_KEEP,
    QUALITY_PRESET_HELP,
    QUALITY_PRESET_LABEL,
    RUNS_TO_KEEP_HELP,
    RUNS_TO_KEEP_LABEL,
    QualityPresetName,
    SettingGroup,
)
from pyrobardfx.store.constants import EXTRA_FORBID


class SettingMeta:
    """Builds the Field metadata every setting carries: its label key, help key and group."""

    @staticmethod
    def of(label_key: str, help_key: str, group: SettingGroup) -> JsonDict:
        return {LABEL_KEY: label_key, HELP_KEY: help_key, GROUP_KEY: group.value}


class Settings(BaseModel):
    """Every setting of the app; each field has a default, so a partial JSON object validates."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    runs_to_keep: int = Field(
        default=DEFAULT_RUNS_TO_KEEP,
        ge=MIN_RUNS_TO_KEEP,
        json_schema_extra=SettingMeta.of(RUNS_TO_KEEP_LABEL, RUNS_TO_KEEP_HELP, SettingGroup.RUNS),
    )
    quality_preset: QualityPresetName = Field(
        default=QualityPresetName.BALANCED,
        json_schema_extra=SettingMeta.of(
            QUALITY_PRESET_LABEL, QUALITY_PRESET_HELP, SettingGroup.RENDER
        ),
    )
