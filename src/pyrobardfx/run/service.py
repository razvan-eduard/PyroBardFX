"""The Run service: takes a Story through every stage into a new Run folder."""

import structlog
from structlog.typing import FilteringBoundLogger

from pyrobardfx.clock.base import Clock
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.run.constants import RUN_ID_ATTEMPTS, SNAPSHOT_FILE
from pyrobardfx.run.pipeline import Pipeline
from pyrobardfx.run.run_id import RunId
from pyrobardfx.run.snapshot import RunSnapshot, RunSnapshotBuilder
from pyrobardfx.run.tokens import TokenSource
from pyrobardfx.store.json_store import JsonStore
from pyrobardfx.trash.base import Trash
from pyrobardfx.workdir.run_folders import RunFolder, RunFolders, RunFolderTakenError
from pyrobardfx.workdir.working_directory import WorkingDirectory


class RunService:
    """Starts Runs in one working directory."""

    def __init__(
        self, working: WorkingDirectory, clock: Clock, tokens: TokenSource, trash: Trash
    ) -> None:
        self._folders = RunFolders(working, RunId.matches, trash)
        self._clock = clock
        self._tokens = tokens

    def start(self, story: str) -> RunFolder:
        """Run the Story into a new Run folder, or raise `RefusedError` touching no earlier Run."""
        snapshot, folder = self._create(story)
        JsonStore(folder.path / SNAPSHOT_FILE, snapshot).write(snapshot)
        with self._folders.log(folder) as handle:
            log: FilteringBoundLogger = structlog.wrap_logger(
                structlog.WriteLogger(handle), processors=[structlog.processors.JSONRenderer()]
            )
            for stage in Pipeline.stages(snapshot, log, self._clock):
                stage.run()
        return folder

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
        return snapshot, self._folders.create(story, run_id, snapshot.runs_to_keep)
