# PyroBardFX

Python-native app that turns a narrated story (a script, a voice recording, or both) into one or more audio-reactive videos with narration, sound design and generated visuals.

## Language

### Time units

**Story**:
One narrated work, the whole of what a run reads: its script, its recording, its settings and its sound and picture plans.
_Avoid_: project, episode, book

**Video**:
One output file of a Story. A Story is exported as one Video or as a series of them; a Video covers whole Chapters.
_Avoid_: export, render, part

**Chapter**:
The largest division inside a Story, opened by a level-one heading (`# Title`) or a `[chapter: Title]` tag; never inferred from silence.
_Avoid_: part, episode, act

**Section**:
A division inside a Chapter, opened by a level-two heading, a `---` or `***` line, a `[section …]` tag, or a voice silence of at least 2.5 s.
_Avoid_: segment, block, passage

**Paragraph**:
A blank-line block of the script; the unit the autotagger reasons about. In an audio-only Story paragraphs are cut from the transcript.
_Avoid_: segment, chunk (that is a render window)

**Scene**:
A stretch of a Story with one visual, bounded by `[scene]` tags or the scene planner, never shorter than the minimum scene length.
_Avoid_: shot, clip (that is the rendered output of a diffusion scene), cut

**Granularity**:
How often a picture, an ambience bed or an underscore changes: per video, story, chapter, section, paragraph or scene, or often (about every minute).
_Avoid_: frequency, change rate, cadence

### Runs

**Run**:
One execution of a Story's pipeline from script or recording to its Videos, identified by a run id and recorded in its own run folder.
_Avoid_: job (that is the worker's unit, a Run is one kind of job), build (as a word for a Run; builder classes and `build()` are about objects), render (that is one stage of a Run)

**Run folder**:
The folder of one Run holding every file the Run wrote: its snapshot, tags, cues, scenes, final script, mix and Videos.
_Avoid_: output folder, workspace

**Run id**:
The name of a Run and of its Run folder: the UTC time the Run started plus four random hex characters (`20261109T153000Z-a1b2`), so run ids sort by start time.
_Avoid_: run number, job id

**Run snapshot**:
The frozen set of values one Run reads, built once at Run start and handed to every Stage; its copy in the Run folder is a record no Stage reads back (ADR 0002).
_Avoid_: run config, run context, run settings

**Stage**:
One step of a Run, in the fixed order every Run passes; each holds the Run snapshot from its start.
_Avoid_: step (that is a progress callback inside a Stage), node, phase

**Pipeline event**:
One structured record of a Run's event stream: the event name, the Stage it came from, the percent that Stage got to, its UTC time and the event's own fields.
_Avoid_: log line, message
"Message" is avoided for a Pipeline event only: the user-facing text of an error or a locale string may still be called a message, so `*_MESSAGE` constant names stay.

**Event fan-out**:
The one structlog logger of a Run's event stream that stamps every Pipeline event with the clock's UTC time and hands it to every Event sink; a Stage emits through it without knowing the sinks.
_Avoid_: event bus, broker, dispatcher

**Event sink**:
One end of the Event fan-out that takes every Pipeline event: the `run.log` JSON lines file, the CLI printer, later the job websocket. A sink that fails is reported once and gets no further events; the Run and the other sinks go on.
_Avoid_: handler, listener, subscriber

**Cancel token**:
What a Run asks at each cancel check whether it was asked to stop; the job manager holds the other end. A Run asked to stop ends at its next check and keeps its Run folder whole.
_Avoid_: kill switch, abort flag, stop signal

**Latest pointer**:
The file in a Story's folder that names the run id of its newest Run.
_Avoid_: current run, symlink

**Review**:
The stop before rendering where a Run waits for the user when a sound tag is red, the narration match is low, or a visual's model is missing; the user resumes or cancels.
_Avoid_: pre-flight, check, approval

**Red tag**:
A sound tag for which the library offered no acceptable sound.
_Avoid_: missing sound, unmatched tag

**Setup change**:
Any action that alters what a Run can use: a model download or install, a library rebuild, a settings-affecting install. A Setup change and a Run never overlap.
_Avoid_: maintenance, admin action

### Mix

**Layer**:
One line of the final mix, of one Layer kind, with its own level, mute, solo and fade; sounds on a Layer play at layer level x tag volume x fade x duck.
_Avoid_: track, channel, bus

**Layer kind**:
A named configuration that defines a family of Layers: its role (voice, bed or one-shot), default level and fade, what it ducks on and how deep, its level band and the script tag that feeds it. New kinds come from config, not code.
_Avoid_: track type, category (that is a sound-library grouping)

**Bed**:
A long sound that loops under the narration: ambience for the whole story, inline atmosphere, underscore or music.
_Avoid_: loop, background, pad

**One-shot**:
A sound played once at a point in time: an effect or a transition.
_Avoid_: hit, sample, SFX (as a kind name)

**Duck**:
A bed's dip while a trigger is heard (the voice, a section break, a one-shot, another layer), by its depth, returning over its release; the deepest trigger wins.
_Avoid_: sidechain, compression

**Fade**:
A short, medium or long ramp at both ends of a sound, as a share of the sound's length; a tag's fade word sets it per sound.
_Avoid_: crossfade (that is only a bed change or a scene change)

**Loudness target**:
The integrated loudness and true peak the final mix is normalised to.
_Avoid_: volume target, gain

### Visuals

**Visual source**:
The kind of picture a Scene shows: a diffusion clip, a still, or geometry. Chosen per Scene, with a story-wide default.
_Avoid_: mode, renderer, engine (that is the library behind a source)

**Clip**:
A short animated sequence made by the diffusion model for one Scene.
_Avoid_: video (that is an output file), animation

**Still**:
A single generated picture that slowly moves for the length of its Scene.
_Avoid_: image, frame, photo

**Geometry**:
A visual computed from shaders or tensor functions rather than a model: fractals, kaleidoscopes, flow fields, reaction-diffusion; usable as a Scene's source or as an overlay under or over another source.
_Avoid_: procedural, generative art, effect

**Look**:
A named table that maps audio features and a style to picture parameters: shader or warp settings, colour, bloom, pulse. Shipped as data and extendable by the user.
_Avoid_: style (that is the prompt wording), theme, filter

**Audio feature**:
A per-frame measurement of the final mix (level, onsets, brightness, band energies, beat phase) that a Look reads.
_Avoid_: analysis, envelope

**Quality preset**:
A named level (fast, balanced, best) that fills the render settings of every Visual source for a Run; the Story may override single fields.
_Avoid_: profile, mode

**Upscale**:
The stage that brings a rendered Clip or Still from its render size to the Video's output size.
_Avoid_: resize (that is the plain Lanczos path, one way to Upscale), enhance

**Text tag**:
A script tag that puts text on the screen for a span of time, drawn as an overlay.
_Avoid_: caption, subtitle (that is the `.srt`), title card

### Sounds

**Sound library**:
The folder tree of sounds a Story's sound design draws from, grouped by Layer kind and category, with one sound index.
_Avoid_: SFX folder, sound pack, samples

**Category**:
A named group of sounds inside a kind (a mood for beds, a family for effects, a type for transitions).
_Avoid_: folder (that is where it lives), tag

**Generated sound**:
A sound made by the text-to-audio model from a prompt; once kept it lives in the Sound library like any other sound.
_Avoid_: AI sound, synthetic sound

**Reviewed**:
A sound the user has listened to and confirmed matches its name and category. An unreviewed sound still plays.
_Avoid_: approved, verified

**Weak match**:
A library sound whose match score for a tag passed the kind's floor but by little; marked apart so the user can retarget or generate.
_Avoid_: yellow (that is the colour), low match (that is the narration score)

**Narration match**:
The share of script words heard in the recording; a low share stops the Run at the Review.
_Avoid_: alignment score, accuracy

**Sound identity**:
What makes two files the same sound to the index: size, modification time, inode and birth time. Never the path, never the change time.
_Avoid_: fingerprint, hash (that is the content id)

**Content id**:
A short hash of a sound's bytes, written after its path in the final script so a moved file is still found.
_Avoid_: sound id, checksum

### Story kinds

**Content type**:
A data-defined family of stories (drug story, scary story, book chapter) that brings its styles, keyword maps, default Look and sound mix; `auto` lets the model pick.
_Avoid_: genre, template, preset

**Video split**:
The Story setting that decides how Chapters are packed into Videos: one, per chapter, or by a maximum length; a `[video]` tag forces a break.
_Avoid_: episode split, export mode

**Bookends**:
The intro and outro added to every Video.
_Avoid_: intro/outro (as two terms), jingle

### Files

**Working directory**:
The one folder the app owns, holding every Story, the Sound library, the models, the settings and the caches. Created on first start in the platform's default place or where the user points it, and never inside a temporary folder.
_Avoid_: workspace, project folder, data dir

**Store**:
A hand-readable JSON file behind a pydantic model with one writer, replaced whole on every write and read from memory; the settings and the library index are stores.
_Avoid_: database, cache (that is data the app can make again)

**Setup preset**:
A named set of settings saved as partial JSON in the working directory: it holds only the fields it sets, and loading it gives the defaults with those fields over them. One Setup preset may be the default, which a working directory without a settings file starts from.
_Avoid_: profile, template, Quality preset (that is a render level)

**Settings stamp**:
The settings a script records: only the fields that differ from the defaults.
_Avoid_: settings dump, config header

**Setting definition**:
What a settings card needs to show one setting (its label key, help key, group, kind, default and constraints), produced from the settings model's JSON schema.
_Avoid_: setting spec, field info

### Models

**Adapter**:
The one class a model sits behind. Each adapter family has one base class that owns the backend, dtype, load, release, timing, progress steps and cancel checks; each runtime is one subclass that declares the backends it runs on and its dtype on each, and each family has one fake.
_Avoid_: wrapper, driver, plugin

**Backend**:
Where a model runs: MPS or MLX on Apple Silicon, CUDA on NVIDIA, or the CPU. The device resolver orders the backends a machine offers, best first, once at startup; the CPU closes every order.
_Avoid_: platform (that is the operating system), runtime (that is the library behind an adapter)

**Device**:
The user's choice of Backend: `auto`, or one backend, given by the `--device` flag or the device setting; the flag wins. A named backend is the only one tried before the CPU.
_Avoid_: GPU, hardware

**Model slot**:
The one place a model is held in memory between stages: loading the next model releases the held one first, so a 16 GB machine finishes a Run.
_Avoid_: model cache, pool
