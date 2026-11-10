"""Constants of the refusal area."""

from enum import StrEnum

REFUSED_MESSAGE = "{reason}: {path} ({detail})"


class RefusalReason(StrEnum):
    """Why a start or a Run was refused; each value is the key of its user-facing text."""

    IN_TEMP = "workdir.refused.in_temp"
    CANNOT_CREATE = "workdir.refused.cannot_create"
    NO_STORY = "run.refused.no_story"
    RUN_ID_TAKEN = "run.refused.run_id_taken"
    PRESET_NAME_TAKEN = "settings.refused.preset_name_taken"
    PRESET_UNKNOWN = "settings.refused.preset_unknown"
