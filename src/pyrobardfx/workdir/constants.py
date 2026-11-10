"""Constants of the working directory area."""

from pathlib import Path

APP_FOLDER_NAME = "PyroBardFX"
DOCUMENTS_FOLDER_NAME = "Documents"
HOME_OVERRIDE_ENV = "PYROBARDFX_HOME"
DOCUMENTS_PLATFORMS = frozenset({"darwin", "win32"})
STORIES_FOLDER = "stories"
RUNS_FOLDER = "runs"
CONFIG_FOLDER = "config"
LAYOUT = (
    CONFIG_FOLDER,
    STORIES_FOLDER,
    "library",
    "models",
    "cache",
    "looks",
    "content_types",
    "locales-override",
)
TEMP_ENV_VARS = ("TMPDIR", "TEMP", "TMP")
FIXED_TEMP_ROOTS = (Path("/tmp"), Path("/var/tmp"))


EVENT_CREATED = "working_directory_created"
EVENT_OPENED = "working_directory_opened"

RUN_LOG_FILE = "run.log"
APPEND_MODE = "a"
LATEST_POINTER_FILE = "latest.json"
PARENT_FOLDER_NAME = ".."
STORY_NAME_PARTS = 1
