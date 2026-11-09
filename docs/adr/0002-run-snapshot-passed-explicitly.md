# A Run reads one snapshot passed explicitly

A Run reads its settings only from one frozen run snapshot. The snapshot is built once at Run start from
the settings files, the Story and any overrides, then passed as an argument to every stage. No stage
reads a module global, and no stage reads a settings file again while the Run is in progress.

This carries over ADR 0002 of the predecessor node pack. There the snapshot travelled between nodes as a
link in the ComfyUI graph; here it is an immutable Python object handed down the pipeline.

## Considered Options

- **Explicit frozen snapshot (chosen).** Every stage sees the same values for the whole Run. A test
  builds a snapshot and calls one stage directly, with no setup of hidden state. The copy written to the
  Run folder records exactly what the Run used.
- **Module-level state.** Rejected. In the predecessor, cached module state missed settings changes,
  and overrides produced bugs that depended on import order and call order and were hard to trace.
- **A run id, with each stage reading the snapshot from disk.** Rejected. Each stage would read a file
  that could be stale or replaced while the Run is in progress, so the Run would depend on file timing
  instead of on one value fixed at its start.

## Consequences

- Every stage takes the snapshot as a parameter; adding a setting never needs a new global.
- A settings change made while a Run is in progress takes effect from the next Run.
- The Run folder holds a copy of the snapshot as a record, but no stage reads that copy back.
- A resumed Run after a Review continues with the snapshot it started with.
