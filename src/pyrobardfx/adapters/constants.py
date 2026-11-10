"""Constants of the model adapters area: backends, dtypes, families and their events."""

from enum import StrEnum


class Backend(StrEnum):
    """Where a model runs; each value is also its name for `--device` and the device setting."""

    MPS = "mps"
    MLX = "mlx"
    CUDA = "cuda"
    CPU = "cpu"


class DeviceChoice(StrEnum):
    """What `--device` or the device setting asks for: one backend, or `auto` for the resolver."""

    AUTO = "auto"
    MPS = Backend.MPS.value
    MLX = Backend.MLX.value
    CUDA = Backend.CUDA.value
    CPU = Backend.CPU.value


class DType(StrEnum):
    """The number type a model's weights and activations use on one backend."""

    FLOAT32 = "float32"
    FLOAT16 = "float16"
    BFLOAT16 = "bfloat16"
    INT8 = "int8"
    INT4 = "int4"


class AdapterFamily(StrEnum):
    """A kind of model adapter; each family has one base class and one fake."""

    STT = "stt"
    TTS = "tts"
    LLM = "llm"
    CLAP = "clap"
    SOUND_GENERATOR = "sound_generator"
    DIFFUSION = "diffusion"
    STILL = "still"
    GEOMETRY = "geometry"
    UPSCALER = "upscaler"


# The accelerators the resolver tries, best first: Apple Silicon (MLX, then MPS), then CUDA.
# The CPU closes every order, so a family that may run there always finds a backend.
ACCELERATORS = (Backend.MLX, Backend.MPS, Backend.CUDA)
# The families that refuse the CPU even when they could run there: a CPU Run of theirs would
# take many hours, so the user gets a clear refusal instead (story 13).
CPU_REFUSING_FAMILIES = frozenset({AdapterFamily.DIFFUSION, AdapterFamily.SOUND_GENERATOR})
# The runtimes the system device probe asks, imported only when it asks, never at module level.
TORCH_MODULE = "torch"
MLX_CORE_MODULE = "mlx.core"

# The detail of a refusal for a runtime that declares none of the order's backends, best first.
UNSUPPORTED_DETAIL = "{family}: {backends}"
BACKEND_SEPARATOR = " > "

EVENT_MODEL_LOADED = "model_loaded"
EVENT_MODEL_RELEASED = "model_released"
EVENT_MODEL_STEP = "model_step"
