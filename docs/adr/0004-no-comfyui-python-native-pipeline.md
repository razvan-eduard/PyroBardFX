# Python-native pipeline, no ComfyUI

The app is a Python-native pipeline. Diffusion runs through diffusers: Clips with AnimateDiff, Stills
with SD 1.5 and SDXL Lightning, and Generated sounds with Stable Audio 3. DSP runs through torchaudio
and pedalboard. There is no ComfyUI process, node graph or custom node anywhere in the app.

Clips keep the predecessor's 16-frame sliding windows and their overlap through a port of
AnimateDiff-Evolved's uniform context scheduler onto the diffusers UNet.

The predecessor was a ComfyUI node pack. It is reference material only: its behaviour informs the
design, and none of its code is imported or run.

## Considered Options

- **Python-native pipeline (chosen).** One process owns the models, the settings and the Run, and the
  UI is free to follow the app's own needs.
- **Keep ComfyUI as the render backend over HTTP.** Rejected. It means two processes to start, watch
  and keep in step, model folders owned by another tool (against ADR 0001), and a UI bound to the shape
  of ComfyUI's.
- **FreeNoise instead of the context scheduler port.** Rejected. diffusers ships FreeNoise, so it would
  cost less to adopt, but its windowing differs from the predecessor's. The port was chosen for
  faithfulness to the predecessor's 16-frame sliding windows and overlap.

## Consequences

- The app owns the context scheduler port and must keep it working as the diffusers UNet changes, so
  the diffusers version is pinned.
- Every feature the predecessor got from a ComfyUI node is rebuilt as app code or taken from a Python
  library; nothing is borrowed from a running ComfyUI.
- Comparisons with the predecessor are made by running both side by side, never by calling one from
  the other.
