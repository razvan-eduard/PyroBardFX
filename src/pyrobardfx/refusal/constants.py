"""Constants of the refusal area."""

from enum import StrEnum

REFUSED_MESSAGE = "{reason}: {path} ({detail})"
# The message of a refusal that concerns no path, such as a device or a model's backend.
REFUSED_WITHOUT_PATH_MESSAGE = "{reason}: {detail}"


class RefusalReason(StrEnum):
    """Why a start or a Run was refused; each value is the key of its user-facing text."""

    IN_TEMP = "workdir.refused.in_temp"
    CANNOT_CREATE = "workdir.refused.cannot_create"
    NO_STORY = "run.refused.no_story"
    RUN_ID_TAKEN = "run.refused.run_id_taken"
    PRESET_NAME_TAKEN = "settings.refused.preset_name_taken"
    PRESET_UNKNOWN = "settings.refused.preset_unknown"
    DEVICE_UNAVAILABLE = "adapters.refused.device_unavailable"
    BACKEND_UNSUPPORTED = "adapters.refused.backend_unsupported"
    CPU_REFUSED = "adapters.refused.cpu"
    CONTENT_TYPE_INVALID = "content_types.refused.invalid_file"
    CONTENT_TYPE_UNKNOWN = "content_types.refused.unknown"
    AUTO_UNRESOLVED = "content_types.refused.auto_unresolved"
