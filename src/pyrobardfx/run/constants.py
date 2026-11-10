"""Constants of the Run area."""

from pyrobardfx.workdir.constants import STAGE_NAME as WORKING_DIRECTORY_STAGE

RUN_ID_TIME_FORMAT = "%Y%m%dT%H%M%SZ"
RUN_ID_FORMAT = "{time}-{token}"
RUN_ID_TOKEN_BYTES = 2
RUN_ID_TOKEN_HEX_LENGTH = 2 * RUN_ID_TOKEN_BYTES
RUN_ID_PATTERN = rf"\d{{8}}T\d{{6}}Z-[0-9a-f]{{{RUN_ID_TOKEN_HEX_LENGTH}}}"
# How many run ids a Run start draws before it refuses: a clash needs the same second and token.
RUN_ID_ATTEMPTS = 3

DEFAULT_RUNS_TO_KEEP = 5
MIN_RUNS_TO_KEEP = 1
SNAPSHOT_FILE = "snapshot.json"
INVALID_SNAPSHOT_MESSAGE = "run snapshot refuses {fields}: unset or out of range"
FIELD_SEPARATOR = ", "
ERROR_LOCATION_KEY = "loc"

# The stage a Run passes before the harness stages: trashing old Runs down to the keep count.
PRUNE_STAGE = "prune_runs"

# The predecessor's self-test harness order; every Run passes the stages in this order.
STAGE_ORDER = (
    WORKING_DIRECTORY_STAGE,
    "settings",
    "tagging_or_reconcile",
    "snapshot",
    "voice_and_alignment",
    "sound_design_and_mix",
    "scenes_and_look",
    "final_script_and_review",
    "render_in_chunks",
    "audio_reactive_fx",
    "upscale",
    "mux_and_subtitles",
    "export_per_video",
)
EVENT_STAGE_STARTED = "stage_started"
EVENT_STAGE_FINISHED = "stage_finished"
EVENT_RUN_CANCELLED = "run_cancelled"
