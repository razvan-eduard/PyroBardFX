"""The Run service: takes a Story through every stage into a new Run folder."""

from dataclasses import dataclass

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.fan_out import EventFanOut
from pyrobardfx.events.sinks import JsonLinesSink
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.cancel import CancelToken, RunCancelledError
from pyrobardfx.run.constants import PRUNE_STAGE, RUN_ID_ATTEMPTS, SNAPSHOT_FILE
from pyrobardfx.run.pipeline import Pipeline
from pyrobardfx.run.pruning import PruneRunsStage
from pyrobardfx.run.run_id import RunId
from pyrobardfx.run.snapshot import RunSnapshot, RunSnapshotBuilder
from pyrobardfx.run.stage import StageDependencies
from pyrobardfx.run.tokens import TokenSource
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
    """Starts Runs in one working directory; each Run's events also go to its `run.log`."""

    def __init__(
        self,
        working: WorkingDirectory,
        clock: Clock,
        tokens: TokenSource,
        trash: Trash,
        events: EventFanOut,
        cancel: CancelToken,
    ) -> None:
        self._folders = RunFolders(working, RunId.matches, trash)
        self._clock = clock
        self._tokens = tokens
        self._events = events
        self._cancel = cancel

    def start(self, story: str) -> RunOutcome:
        """Run the Story into a new Run folder, or raise `RefusedError` touching no earlier Run.

        A Run asked to stop ends at its next cancel check and keeps its Run folder whole.
        """
        snapshot, folder = self._create(story)
        JsonStore(folder.path / SNAPSHOT_FILE, snapshot).write(snapshot)
        with self._folders.log(folder) as handle:
            events = self._events.with_sink(JsonLinesSink(handle))
            dependencies = StageDependencies(snapshot, events, self._clock, self._cancel)
            prune = PruneRunsStage(PRUNE_STAGE, dependencies, self._folders)
            try:
                Pipeline.harness(dependencies, prune).run(folder)
            except RunCancelledError:
                return RunOutcome(folder, cancelled=True)
        return RunOutcome(folder, cancelled=False)

    def _create(self, story: str) -> tuple[RunSnapshot, RunFolder]:
        """Draw run ids until one has no Run folder yet; refuse after `RUN_ID_ATTEMPTS` draws."""
        for _ in range(RUN_ID_ATTEMPTS - 1):
            try:
                return self._create_once(story)
            except RunFolderTakenError:
                continue
        try:
            return self._create_once(story)
        except RunFolderTakenError as error:
            raise RefusedError(RefusalReason.RUN_ID_TAKEN, error.runs, error.run_id) from error

    def _create_once(self, story: str) -> tuple[RunSnapshot, RunFolder]:
        run_id = RunId.draw(self._clock, self._tokens)
        snapshot = RunSnapshotBuilder().story(story).run_id(run_id).build()
        return snapshot, self._folders.create(story, run_id)
