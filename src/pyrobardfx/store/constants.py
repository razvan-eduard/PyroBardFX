"""Constants of the store area."""

from typing import Final

ENCODING = "utf-8"
JSON_INDENT = 2
LINE_END = "\n"
DUMP_MODE = "json"
WRITE_MODE = "w"
TEMP_NAME = ".{name}.{token}.tmp"
TEMP_TOKEN_BYTES = 4
# A broken file set aside onto a taken backup name goes to `<stem>-2`, `<stem>-3` and so on.
NUMBERED_BACKUP_STEM = "{stem}-{number}"
FIRST_NUMBERED_BACKUP = 2
# A stored model refuses fields it does not know, so a mistyped key never passes silently.
EXTRA_FORBID: Final = "forbid"
# A model validator that runs on the built model, after its fields validated.
VALIDATE_AFTER: Final = "after"
