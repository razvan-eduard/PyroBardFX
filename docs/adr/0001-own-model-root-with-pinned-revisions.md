# Models live under our own root with pinned revisions

Every model the app uses lives only under `<working dir>/models/<folder key>/`. A model is fetched with
`huggingface_hub.snapshot_download(revision=<hash>)` at a pinned revision, and every file is hashed with
sha256 and compared to the expected value before first use. Nothing is shared with other installs: a
fresh install downloads every model again, even when the same weights already sit on the disk.

This supersedes ADR 0001 of the predecessor node pack, which reused the model folders of the ComfyUI
install it ran inside.

## Considered Options

- **Own root, pinned revision, sha256 (chosen).** The app owns the layout, so a folder key always means
  the same files. A pinned revision makes a model reproducible across machines and over time, and the
  hash catches a partial or altered download. The cost is disk space and download time on a machine
  that already holds the weights.
- **Reuse existing ComfyUI or Hugging Face cache folders.** Rejected. It couples the app to another
  tool's folder layout, which that tool may change without notice. Files placed there by hand or by
  another tool carry no revision and no hash, so the app cannot tell which weights it is loading.
- **A symlink farm into those folders.** Rejected. It keeps the same coupling and the same unknown
  origin of the files, and adds links that break silently when the other tool moves or deletes a file.

## Consequences

- The working directory grows by the full size of every model the user installs.
- A model download is a Setup change, so it never overlaps a Run.
- Moving the working directory moves the models with it; the app reads no model path outside it.
- Tests inject the working directory and use fake models; no test downloads anything.
