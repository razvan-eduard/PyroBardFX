"""The Run factory: the one wiring of a Run that the CLI and the web routes share."""

from collections.abc import Callable, Sequence
from typing import Protocol

from pyrobardfx.adapters.constants import DeviceChoice
from pyrobardfx.adapters.devices import DeviceProbe, DeviceResolver
from pyrobardfx.clock.base import Clock
from pyrobardfx.domain.constants import StageName
from pyrobardfx.domain.tokens import TokenSource
from pyrobardfx.events.fan_out import ErrorStream, EventFanOut, EventSink, StageEvents
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.cancel import CancelToken
from pyrobardfx.run.service import RunOutcome, RunService
from pyrobardfx.run.settings_stage import SettingsStage
from pyrobardfx.settings.service import SettingsService
from pyrobardfx.trash.base import Trash
from pyrobardfx.workdir.working_directory import WorkingDirectory


class RunSpeaker(EventSink, ErrorStream, Protocol):
    """Speaks a Run to its user in one language: each event, and each failed sink's report."""


class ReadyRun[S: RunSpeaker]:
    """A Run wired over one working directory's settings, speaking through `speaker`."""

    def __init__(
        self, speaker: S, runs: RunService, settings: SettingsService, unsent: StageEvents
    ) -> None:
        self.speaker = speaker
        self._runs = runs
        self._settings = settings
        self._unsent = unsent

    def start(self, story: str) -> RunOutcome:
        """Run the Story as `RunService.start` does; each set-aside settings record goes out once.

        A Run refused, or cancelled before its settings stage, sends the records that stage would
        have sent, then raises or returns.
        """
        try:
            outcome = self._runs.start(story)
        except RefusedError:
            SettingsStage.replay(self._settings, self._unsent)
            raise
        if outcome.cancelled:
            SettingsStage.replay(self._settings, self._unsent)
        return outcome


class RunFactory:
    """Readies Runs over the app's adapters; each Run's events go to its speaker and `sinks`.

    `devices` is asked which backends the machine offers, at each Run start.
    """

    def __init__(
        self,
        clock: Clock,
        tokens: TokenSource,
        trash: Trash,
        cancel: CancelToken,
        labels: Labels,
        devices: DeviceProbe,
        sinks: Sequence[EventSink] = (),
    ) -> None:
        self._clock = clock
        self._tokens = tokens
        self._trash = trash
        self._cancel = cancel
        self._labels = labels
        self._devices = DeviceResolver(devices)
        self._sinks = tuple(sinks)

    def open[S: RunSpeaker](
        self,
        working: WorkingDirectory,
        speaker_for: Callable[[Labels], S],
        device: DeviceChoice = DeviceChoice.AUTO,
    ) -> ReadyRun[S]:
        """Open the settings of `working` and ready a Run whose speaker speaks their `ui_language`.

        `speaker_for` makes the speaker from the labels of that language, read from the locales
        folder of the app's labels. `device` wins over the device setting unless it is `auto`.
        """
        # The settings stage replays each set-aside event into the Run, which also logs it to
        # `run.log`; opening on a fan-out without sinks makes a replay the only send.
        silent = EventFanOut(self._clock, (), speaker_for(self._labels), self._labels)
        settings = SettingsService.open(working, self._clock, silent)
        speaking = self._labels.for_language(settings.read().ui_language)
        speaker = speaker_for(speaking)
        events = EventFanOut(self._clock, (speaker, *self._sinks), speaker, speaking)
        runs = RunService(
            working,
            self._clock,
            self._tokens,
            self._trash,
            events,
            self._cancel,
            settings,
            self._devices,
            device,
        )
        return ReadyRun(speaker, runs, settings, events.at(StageName.SETTINGS))
