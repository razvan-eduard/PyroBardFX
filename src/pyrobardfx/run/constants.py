"""Constants of the Run area."""

from pyrobardfx.domain.constants import StageName

# How many run ids a Run start draws before it refuses: a clash needs the same second and token.
RUN_ID_ATTEMPTS = 3
NO_RUN_ID_ATTEMPT_MESSAGE = "a Run start drew no run id: RUN_ID_ATTEMPTS is below one"

SNAPSHOT_FILE = "snapshot.json"
INVALID_SNAPSHOT_MESSAGE = "run snapshot refuses {fields}: unset or out of range"

# The predecessor's self-test harness order; every Run passes the stages in this order.
STAGE_ORDER = (
    StageName.WORKING_DIRECTORY_OPEN,
    StageName.SETTINGS,
    StageName.TAGGING_OR_RECONCILE,
    StageName.SNAPSHOT,
    StageName.VOICE_AND_ALIGNMENT,
    StageName.SOUND_DESIGN_AND_MIX,
    StageName.SCENES_AND_LOOK,
    StageName.FINAL_SCRIPT_AND_REVIEW,
    StageName.RENDER_IN_CHUNKS,
    StageName.AUDIO_REACTIVE_FX,
    StageName.UPSCALE,
    StageName.MUX_AND_SUBTITLES,
    StageName.EXPORT_PER_VIDEO,
)
EVENT_STAGE_STARTED = "stage_started"
EVENT_STAGE_FINISHED = "stage_finished"
EVENT_RUN_CANCELLED = "run_cancelled"
