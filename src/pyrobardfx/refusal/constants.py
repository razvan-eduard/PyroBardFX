"""Constants of the refusal area."""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Final

REFUSED_MESSAGE = "{reason}: {path} ({detail})"
# The message of a refusal that concerns no path, such as a device or a model's backend.
REFUSED_WITHOUT_PATH_MESSAGE = "{reason}: {detail}"
# Each literal value a refusal's message adds after the rest, quoted so an empty value shows.
REFUSED_LITERAL_MESSAGE = " {name}={value!r}"
# A refusal built with a placeholder in both `labelled` and `literal`: a programming error.
CLAIMED_TWICE_MESSAGE = "placeholders in both labelled and literal: {names}"
# A refusal built with other further placeholders than its reason's text needs.
WRONG_PLACEHOLDERS_MESSAGE = "{reason} needs the placeholders {needed}, was given {given}"
# The placeholders the renderer fills for every refusal text: the refusal's path and detail, the
# working directory option and the home override environment variable.
PATH_FIELD = "path"
DETAIL_FIELD = "detail"
OPTION_FIELD = "option"
ENV_FIELD = "env"
FIXED_PLACEHOLDERS: Final = frozenset({PATH_FIELD, DETAIL_FIELD, OPTION_FIELD, ENV_FIELD})
# The placeholder of a refusal text that names the family, in the user's words.
FAMILY_FIELD = "family"
# The placeholder of the unknown Content type refusal that names the creator's choice as typed.
CHOICE_FIELD = "choice"


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


# The further placeholders each reason's text holds beyond the fixed ones; a reason not listed
# holds none.
FURTHER_PLACEHOLDERS: Final[Mapping[RefusalReason, frozenset[str]]] = MappingProxyType(
    {
        RefusalReason.CPU_REFUSED: frozenset({FAMILY_FIELD}),
        RefusalReason.BACKEND_UNSUPPORTED: frozenset({FAMILY_FIELD}),
        RefusalReason.CONTENT_TYPE_UNKNOWN: frozenset({CHOICE_FIELD}),
    }
)
