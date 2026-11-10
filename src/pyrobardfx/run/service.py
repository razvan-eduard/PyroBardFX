"""The Run service: takes a Story through every stage into a new Run folder."""

from dataclasses import dataclass

from pyrobardfx.adapters.constants import DeviceChoice
from pyrobardfx.adapters.devices import DeviceResolver
from pyrobardfx.clock.base import Clock
from pyrobardfx.domain.constants import StageName
from pyrobardfx.domain.run_id import RunId
from pyrobardfx.domain.tokens import TokenSource
from pyrobardfx.events.fan_out import EventFanOut
from pyrobardfx.events.sinks import JsonLinesSink
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.cancel import CancelToken, RunCancelledError
from pyrobardfx.run.constants import (
    NO_RUN_ID_ATTEMPT_MESSAGE,
    RUN_ID_ATTEMPTS,
    SNAPSHOT_FILE,
)
from pyrobardfx.run.pipeline import Pipeline
from pyrobardfx.run.pruning import PruneRunsStage
from pyrobardfx.run.settings_stage import SettingsStage
from pyrobardfx.run.snapshot import RunSnapshot, RunSnapshotBuilder
from pyrobardfx.run.stage import StageDependencies
from pyrobardfx.settings.service import SettingsService
from pyrobardfx.store.json_store import JsonStore
from pyrobardfx.trash.base import Trash
from pyrobardfx.workdir.run_folders import RunFolder, RunFolders, RunFolderTakenError
from pyrobardfx.workdir.working_directory import WorkingDirectory


@dataclass(frozen=True)
class RunOutcome:
    """How a Run ended: its Run folder, and whether it stopped at a cancel check."""

    folder: RunFolder
    cancelled: bool


class RunService:
    """Starts Runs in one working directory; each Run's events also go to its `run.log`.

    A Run reads the settings once, at its start, into its frozen snapshot (ADR 0002). Its
    backend order is resolved then too, by `devices` from `device` (the `--device` flag) and the
    device setting, and goes into the snapshot beside them.
    """

    def __init__(
        self,
        working: WorkingDirectory,
        clock: Clock,
        tokens: TokenSource,
        trash: Trash,
        events: EventFanOut,
        cancel: CancelToken,
        settings: SettingsService,
        devices: DeviceResolver,
        device: DeviceChoice,
    ) -> None:
        self._folders = RunFolders(working, trash)
        self._clock = clock
        self._tokens = tokens
        self._events = events
        self._cancel = cancel
        self._settings = settings
        self._devices = devices
        self._device = device

    def start(self, story: str) -> RunOutcome:
        """Run the Story into a new Run folder, or raise `RefusedError` touching no earlier Run.

        A device the machine does not offer is refused before the Run folder is made.

        A Run asked to stop ends at its next cancel check and keeps its Run folder whole.
        """
        snapshot, folder = self._create(story)
        JsonStore(folder.path / SNAPSHOT_FILE, snapshot).write(snapshot)
        with self._folders.log(folder) as handle:
            events = self._events.with_sink(JsonLinesSink(handle))
            dependencies = StageDependencies(snapshot, events, self._clock, self._cancel)
            prune = PruneRunsStage(StageName.PRUNE_RUNS, dependencies, self._folders)
            settings = SettingsStage(StageName.SETTINGS, dependencies, self._settings)
            try:
                Pipeline.harness(dependencies, prune, settings).run(folder)
            except RunCancelledError:
                return RunOutcome(folder, cancelled=True)
        return RunOutcome(folder, cancelled=False)

    def _create(self, story: str) -> tuple[RunSnapshot, RunFolder]:
        """Draw run ids until one has no Run folder yet; refuse after `RUN_ID_ATTEMPTS` draws."""
        taken: RunFolderTakenError | None = None
        for _ in range(RUN_ID_ATTEMPTS):
            try:
                return self._create_once(story)
            except RunFolderTakenError as error:
                taken = error
        if taken is None:
            raise RuntimeError(NO_RUN_ID_ATTEMPT_MESSAGE)
        raise RefusedError(RefusalReason.RUN_ID_TAKEN, taken.runs, taken.run_id) from taken

    def _create_once(self, story: str) -> tuple[RunSnapshot, RunFolder]:
        run_id = RunId.draw(self._clock, self._tokens)
        settings = self._settings.read()
        order = self._devices.pick(self._device, settings.device)
        builder = RunSnapshotBuilder().story(story).run_id(run_id).settings(settings)
        snapshot = builder.backend_order(order).build()
        return snapshot, self._folders.create(story, run_id)
