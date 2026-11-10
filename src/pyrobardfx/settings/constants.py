"""Constants of the settings area."""

from enum import StrEnum

from pyrobardfx.locales.constants import Language

SETTINGS_FILE = "settings.json"
PRESETS_FILE = "presets.json"
# A broken store file is kept beside itself under this name, dated by the clock's UTC time.
BACKUP_NAME = "{stem}.broken-{time}{suffix}"

UNKNOWN_DEFAULT_MESSAGE = "the default setup preset {name} is not among the presets"

STAGE_NAME = "settings"
EVENT_SET_ASIDE = "settings_file_set_aside"

DEFAULT_RUNS_TO_KEEP = 5
MIN_RUNS_TO_KEEP = 1

# The keys of a setting's Field metadata in the model's JSON schema.
LABEL_KEY = "label_key"
HELP_KEY = "help_key"
GROUP_KEY = "group"
# The keys of the JSON schema pydantic writes for a model.
PROPERTIES_KEY = "properties"
TYPE_KEY = "type"
DEFAULT_KEY = "default"
MINIMUM_KEY = "minimum"
MAXIMUM_KEY = "maximum"
ENUM_KEY = "enum"
REF_KEY = "$ref"
DEFS_KEY = "$defs"
REF_SEPARATOR = "/"
# Schema constraints a setting definition does not carry; a field holding one is refused, so a
# card never shows looser bounds than the backend checks.
UNMODELLED_CONSTRAINT_KEYS = (
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
)
UNMODELLED_CONSTRAINT_MESSAGE = (
    "the setting {name} has the constraint {key}, which no definition carries"
)

RUNS_TO_KEEP_LABEL = "settings.runs_to_keep.label"
RUNS_TO_KEEP_HELP = "settings.runs_to_keep.help"
QUALITY_PRESET_LABEL = "settings.quality_preset.label"
QUALITY_PRESET_HELP = "settings.quality_preset.help"
UI_LANGUAGE_LABEL = "settings.ui_language.label"
UI_LANGUAGE_HELP = "settings.ui_language.help"
STORY_LANGUAGE_LABEL = "settings.story_language.label"
STORY_LANGUAGE_HELP = "settings.story_language.help"

# The language a fresh working directory speaks and tells its Stories in.
DEFAULT_LANGUAGE = Language.EN


class SettingGroup(StrEnum):
    """The card a setting is shown on."""

    RUNS = "runs"
    RENDER = "render"
    LANGUAGE = "language"


class QualityPresetName(StrEnum):
    """The Quality preset a Run fills its render settings from."""

    FAST = "fast"
    BALANCED = "balanced"
    BEST = "best"
