"""Constants of the store area."""

from typing import Final

ENCODING = "utf-8"
JSON_INDENT = 2
LINE_END = "\n"
DUMP_MODE = "json"
WRITE_MODE = "w"
TEMP_NAME = ".{name}.{token}.tmp"
TEMP_TOKEN_BYTES = 4
# A stored model refuses fields it does not know, so a mistyped key never passes silently.
EXTRA_FORBID: Final = "forbid"
