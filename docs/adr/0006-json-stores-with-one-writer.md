# JSON stores with one writer

The library index and the settings are hand-readable JSON files with one writer. One process owns every
file, and the single anyio worker task serialises all writes. A write turns the pydantic model into
text with `json.dumps`, writes it to a temp file and moves it into place with `os.replace`, which is
atomic, so no lock file is needed. Reads are served from memory.

CLAP embeddings and loudness caches are binary data, so they live in a sidecar `embeddings.safetensors`
keyed by content id, next to the JSON index.

## Considered Options

- **JSON files with one writer (chosen).** The user can open, read and diff every file. One writer
  removes write races, and `os.replace` means a crash leaves either the old file or the new one, never
  half of each.
- **SQLite.** Rejected. Its file is binary and cannot be diffed by the user, and its concurrency
  features are more than one writer needs.
- **TinyDB.** Rejected. It is another dependency layered over JSON with no gain in atomicity.
- **Lock files.** Rejected. A crash leaves a stale lock behind, which then blocks the next start.

## Consequences

- No second process may write these files. A tool that needs to change them goes through the app's
  services.
- Every write is a whole-file write, so the files must stay small enough to rewrite on each change;
  embeddings stay out of the JSON for that reason.
- A sound whose content id is missing from the sidecar has its embedding and loudness computed again.
- Tests inject the working directory and read the written JSON back as plain text.
