"""Constants of the Content types area: where their data files live and how they are named."""

from pathlib import Path

# The shipped Content types, one data file each, in the package so a checkout and an installed
# wheel read the same files. A Content type's name is its file's stem.
SHIPPED_FOLDER = Path(__file__).parent / "data"
DATA_FILE_PATTERN = "*.json"

# The locale key of each shipped Content type's name; its data file's `label_key` names it.
BOOK_CHAPTER_LABEL_KEY = "content_types.book_chapter.label"
DRUG_STORY_LABEL_KEY = "content_types.drug_story.label"
SCARY_STORY_LABEL_KEY = "content_types.scary_story.label"

# The Content type choice that lets the model pick, and the locale key of its name.
AUTO = "auto"
AUTO_LABEL_KEY = "content_types.auto.label"
# A model's answer names a Content type with its words apart: `Scary Story` is `scary_story`.
NAME_WORD_SEPARATOR = "_"
ANSWER_GAP_PATTERN = r"[\s-]+"
# The Content type `auto` takes when the model's answer names none: the predecessor's first one.
FALLBACK_CONTENT_TYPE = "drug_story"
