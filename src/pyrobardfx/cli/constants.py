"""Constants of the command line area."""

from pyrobardfx.refusal.constants import RefusalReason

APP_NAME = "pyrobardfx"
WORKING_DIR_OPTION = "--working-dir"
WORKING_DIR_HELP = "Use this folder as the working directory instead of the default place."
REFUSED_EXIT_CODE = 1
# The exit code of a program stopped by an interrupt, as shells report it.
CANCELLED_EXIT_CODE = 130
RUN_COMMAND = "run"
RUN_HELP = "Take a Story through every stage into a new Run folder."
NO_WORKING_DIRECTORY_MESSAGE = "the run command started without an open working directory"
STORY_HELP = "The name of the Story's folder under stories/ in the working directory."

# English text per refusal key, until the locale files of `label(key)` take these keys over.
CHOOSE_ANOTHER_TEXT = " Choose another place with {option} or {env}."
REFUSAL_TEXT = {
    RefusalReason.IN_TEMP: (
        "Refused working directory {path}: it is inside the temporary folder {detail}, "
        "which the system may empty on reboot." + CHOOSE_ANOTHER_TEXT
    ),
    RefusalReason.CANNOT_CREATE: (
        "Refused working directory {path}: it cannot be created ({detail})." + CHOOSE_ANOTHER_TEXT
    ),
    RefusalReason.NO_STORY: "Refused run: there is no Story named {detail} in {path}.",
    RefusalReason.RUN_ID_TAKEN: (
        "Refused run: every run id drawn, the last {detail}, already has a Run folder in {path}."
    ),
    RefusalReason.PRESET_NAME_TAKEN: (
        "Refused setup preset {detail}: {path} already holds a setup preset of that name."
    ),
    RefusalReason.PRESET_UNKNOWN: (
        "Refused setup preset {detail}: {path} holds no setup preset of that name."
    ),
}
# English text of the key `run.finished`, until `label(key)` and the locales take it.
RUN_FINISHED_TEXT = "Run {run_id} finished: {path}"
# English text of the key `run.cancelled`, until `label(key)` and the locales take it.
RUN_CANCELLED_TEXT = "Run {run_id} cancelled: {path}"
# English text of the key `run.progress`, until `label(key)` and the locales take it:
# one progress line per event, with stage, percent, event name, then each field.
RUN_PROGRESS_TEXT = "{stage} {percent:.0f}% {event}{fields}"
# English text of the key `run.progress_field`, until `label(key)` and the locales take it.
RUN_PROGRESS_FIELD_TEXT = " {key}={value}"
