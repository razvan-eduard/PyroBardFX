"""Constants of the working directory area."""

from enum import StrEnum
from pathlib import Path

APP_FOLDER_NAME = "PyroBardFX"
DOCUMENTS_FOLDER_NAME = "Documents"
HOME_OVERRIDE_ENV = "PYROBARDFX_HOME"
DOCUMENTS_PLATFORMS = frozenset({"darwin", "win32"})
LAYOUT = (
    "config",
    "stories",
    "library",
    "models",
    "cache",
    "looks",
    "content_types",
    "locales-override",
)
TEMP_ENV_VARS = ("TMPDIR", "TEMP", "TMP")
FIXED_TEMP_ROOTS = (Path("/tmp"), Path("/var/tmp"))


REFUSED_MESSAGE = "{reason}: {path} ({detail})"


class RefusalReason(StrEnum):
    """Why a start refuses a working directory; each value is the key of its user-facing text."""

    IN_TEMP = "workdir.refused.in_temp"
    CANNOT_CREATE = "workdir.refused.cannot_create"


LOGGER_NAME = "pyrobardfx.workdir"
STAGE_NAME = "working_directory_open"
EVENT_CREATED = "working_directory_created"
EVENT_OPENED = "working_directory_opened"
PERCENT_DONE = 100.0
