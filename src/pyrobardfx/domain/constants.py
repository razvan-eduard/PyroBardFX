"""Constants of the domain area: the shape of a Run id and the closed set of Stage names."""

from enum import StrEnum

RUN_ID_FORMAT = "{time}-{token}"
RUN_ID_TOKEN_BYTES = 2
RUN_ID_TOKEN_HEX_LENGTH = 2 * RUN_ID_TOKEN_BYTES
RUN_ID_PATTERN = rf"\d{{8}}T\d{{6}}Z-[0-9a-f]{{{RUN_ID_TOKEN_HEX_LENGTH}}}"
NOT_A_RUN_ID_MESSAGE = "{name} is not shaped like a run id"


class StageName(StrEnum):
    """The name of each Stage, in the order a Run passes them; each value is its log string."""

    # The stage a Run passes before the harness stages: trashing old Runs down to the keep count.
    PRUNE_RUNS = "prune_runs"
    WORKING_DIRECTORY_OPEN = "working_directory_open"
    SETTINGS = "settings"
    TAGGING_OR_RECONCILE = "tagging_or_reconcile"
    SNAPSHOT = "snapshot"
    VOICE_AND_ALIGNMENT = "voice_and_alignment"
    SOUND_DESIGN_AND_MIX = "sound_design_and_mix"
    SCENES_AND_LOOK = "scenes_and_look"
    FINAL_SCRIPT_AND_REVIEW = "final_script_and_review"
    RENDER_IN_CHUNKS = "render_in_chunks"
    AUDIO_REACTIVE_FX = "audio_reactive_fx"
    UPSCALE = "upscale"
    MUX_AND_SUBTITLES = "mux_and_subtitles"
    EXPORT_PER_VIDEO = "export_per_video"
