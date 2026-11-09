# Web UI in a pywebview window

The UI is a web front end: Svelte 5, TypeScript and Vite, Konva for the timeline lanes, wavesurfer.js
for waveforms, CodeMirror 6 with a Lezer grammar for script tags, and Web Audio for playback. FastAPI
serves it from a built `dist/`, and a pywebview window shows it from day one. A thin CLI sits over the
same services as the UI.

The reason is the timeline viewer and editor, with one lane per Layer. It is the hardest screen in the
app, and a web stack has the best libraries for it.

## Boundaries

- Python never imports Node. Node is needed only to build `dist/`.
- The OpenAPI schema generates the TypeScript types, so the front end and the API cannot drift apart.
- The pydantic settings model is the one source for the settings defs route and the settings cards.
- The CLI and the UI call the same services; neither holds logic the other lacks.

## Considered Options

- **Web front end in pywebview (chosen).** Best timeline and editor libraries, one window like a
  desktop app, and no second runtime to ship.
- **Qt or Tkinter desktop UI.** Rejected. Their timeline widgets are weak, so the hardest screen would
  be built from scratch.
- **Reuse the predecessor's plain JS.** Rejected. It was not built for a timeline editor and does not
  fit one.
- **Electron.** Rejected. It is a second runtime to ship and update next to Python.

## Consequences

- Building a release needs a Node toolchain, and the release ships the built `dist/`.
- The front end has its own test and build gate next to the Python gates.
