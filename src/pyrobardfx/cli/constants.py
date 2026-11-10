"""Constants of the command line area."""

APP_NAME = "pyrobardfx"
WORKING_DIR_OPTION = "--working-dir"
REFUSED_EXIT_CODE = 1
# The exit code of a program stopped by an interrupt, as shells report it.
CANCELLED_EXIT_CODE = 130
RUN_COMMAND = "run"
NO_WORKING_DIRECTORY_MESSAGE = "the run command started without an open working directory"

# The locale keys of the typer help, which resolves in en when the app is built.
WORKING_DIR_HELP_KEY = "cli.working_dir.help"
RUN_HELP_KEY = "cli.run.help"
STORY_HELP_KEY = "cli.run.story.help"

# The locale keys of the printer lines; a refusal's line is keyed by its `RefusalReason`.
RUN_FINISHED_KEY = "run.finished"
RUN_CANCELLED_KEY = "run.cancelled"
# One progress line per event, with stage, percent, event name, then each field.
RUN_PROGRESS_KEY = "run.progress"
RUN_PROGRESS_FIELD_KEY = "run.progress_field"
