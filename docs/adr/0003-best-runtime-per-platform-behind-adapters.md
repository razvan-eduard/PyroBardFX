# Best runtime per platform behind one adapter per model

Every model or engine sits behind one adapter. Behind that adapter the app uses the fastest measured
runtime for the platform: Metal, MPS or MLX on Apple Silicon, CUDA on NVIDIA, and a CPU fallback
everywhere else. Two or three libraries for one task are accepted when that is what the fastest path on
each platform needs.

Examples: speech to text uses mlx-whisper on macOS and faster-whisper elsewhere; the language model uses
mlx-lm on macOS and llama-cpp-python elsewhere. Callers see one interface per task and never name a
library.

## How the backend is chosen

- One `pick_device()` resolver runs once at startup and returns the backend for the platform.
- Each adapter declares the backends it supports and the dtype it uses on each backend.
- The `--device` flag and a setting override the resolver.
- The self-test records the backend each model ran on.

## Considered Options

- **Fastest runtime per platform behind adapters (chosen).** Each platform gets its best speed, and
  the adapter keeps that choice out of the pipeline code.
- **One portable library per task.** Rejected. Every portable option is slow on at least one
  of the three platforms, and the slow platform pays for it on every Run.
- **ONNX everywhere.** Rejected. Its coverage of diffusion and text to speech models is poor, so the
  heaviest tasks would need a second runtime anyway.

## Consequences

- The app carries more dependencies, some of them installed only on one platform.
- A task with two libraries needs adapter tests for both, with fakes, and one real call to each model in the
  self-test.
- Adding a platform means adding backends to adapters, not changing the pipeline.
