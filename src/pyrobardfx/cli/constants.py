"""Constants of the command line area."""

from pyrobardfx.workdir.constants import RefusalReason

APP_NAME = "pyrobardfx"
WORKING_DIR_OPTION = "--working-dir"
WORKING_DIR_HELP = "Use this folder as the working directory instead of the default place."
REFUSED_EXIT_CODE = 1

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
}
