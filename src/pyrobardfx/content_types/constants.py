"""Constants of the Content types area: where their data files live and how they are named."""

from pathlib import Path

# The shipped Content types, one data file each, in the package so a checkout and an installed
# wheel read the same files. A Content type's name is its file's stem.
SHIPPED_FOLDER = Path(__file__).parent / "data"
DATA_FILE_PATTERN = "*.json"

# The Content type choice that lets the model pick, and the locale key of its name.
AUTO = "auto"
AUTO_LABEL_KEY = "content_types.auto.label"
# A model's answer names a Content type with its words apart: `Scary Story` is `scary_story`.
NAME_WORD_SEPARATOR = "_"
ANSWER_GAP_PATTERN = r"[\s-]+"
# How a skipped file's refusal names a bad field, `styles.fog`, and, for a field-less error such
# as broken JSON, which key of the validation error holds the parser's words.
LOCATION_SEPARATOR = "."
ERROR_MESSAGE_KEY = "msg"
