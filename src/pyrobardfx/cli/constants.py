"""Constants of the command line area."""

from pyrobardfx.refusal.constants import RefusalReason

APP_NAME = "pyrobardfx"
WORKING_DIR_OPTION = "--working-dir"
WORKING_DIR_HELP = "Use this folder as the working directory instead of the default place."
REFUSED_EXIT_CODE = 1
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
}
# English text of the key `run.finished`, until `label(key)` and the locales take it.
RUN_FINISHED_TEXT = "Run {run_id} finished: {path}"
