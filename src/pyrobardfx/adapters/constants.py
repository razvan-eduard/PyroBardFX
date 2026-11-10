"""Constants of the model adapters area: backends, dtypes, families and their events."""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


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
# The Apple Silicon backends: naming one puts it first and keeps the other next, if found.
APPLE_SILICON_TIER = (Backend.MLX, Backend.MPS)
# The families that refuse the CPU even when they could run there: a CPU Run of theirs would
# take many hours, so the user gets a clear refusal instead (story 13).
CPU_REFUSING_FAMILIES = frozenset({AdapterFamily.DIFFUSION, AdapterFamily.SOUND_GENERATOR})
# The runtimes the system device probe asks, imported only when it asks, never at module level.
TORCH_MODULE = "torch"
MLX_CORE_MODULE = "mlx.core"

# The detail of a refusal for a runtime that declares none of the order's backends, best first.
BACKEND_SEPARATOR = " > "
# The placeholder of a refusal text that names the family, in the user's words.
FAMILY_FIELD = "family"

STT_LABEL_KEY = "adapters.family.stt"
TTS_LABEL_KEY = "adapters.family.tts"
LLM_LABEL_KEY = "adapters.family.llm"
CLAP_LABEL_KEY = "adapters.family.clap"
SOUND_GENERATOR_LABEL_KEY = "adapters.family.sound_generator"
DIFFUSION_LABEL_KEY = "adapters.family.diffusion"
STILL_LABEL_KEY = "adapters.family.still"
GEOMETRY_LABEL_KEY = "adapters.family.geometry"
UPSCALER_LABEL_KEY = "adapters.family.upscaler"
# Each family's name in the user's words, as a refusal shows it.
FAMILY_LABEL_KEYS: Mapping[AdapterFamily, str] = MappingProxyType(
    {
        AdapterFamily.STT: STT_LABEL_KEY,
        AdapterFamily.TTS: TTS_LABEL_KEY,
        AdapterFamily.LLM: LLM_LABEL_KEY,
        AdapterFamily.CLAP: CLAP_LABEL_KEY,
        AdapterFamily.SOUND_GENERATOR: SOUND_GENERATOR_LABEL_KEY,
        AdapterFamily.DIFFUSION: DIFFUSION_LABEL_KEY,
        AdapterFamily.STILL: STILL_LABEL_KEY,
        AdapterFamily.GEOMETRY: GEOMETRY_LABEL_KEY,
        AdapterFamily.UPSCALER: UPSCALER_LABEL_KEY,
    }
)

EVENT_MODEL_LOADED = "model_loaded"
EVENT_MODEL_RELEASED = "model_released"
EVENT_MODEL_STEP = "model_step"
