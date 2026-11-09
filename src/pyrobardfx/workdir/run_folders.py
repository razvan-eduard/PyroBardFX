"""The Run folders of the Stories in one working directory."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from pydantic import BaseModel, ConfigDict

from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.store.constants import ENCODING, EXTRA_FORBID
from pyrobardfx.store.json_store import JsonStore
from pyrobardfx.trash.base import Trash
from pyrobardfx.workdir.constants import (
    APPEND_MODE,
    LATEST_POINTER_FILE,
    PARENT_FOLDER_NAME,
    RUN_LOG_FILE,
    RUNS_FOLDER,
    STORIES_FOLDER,
    STORY_NAME_PARTS,
)
from pyrobardfx.workdir.working_directory import WorkingDirectory


@dataclass(frozen=True)
class RunFolder:
    """The folder of one Run, holding every file the Run writes."""

    run_id: str
    path: Path


class RunFolderTakenError(Exception):
    """A Run folder of that run id already exists; nothing was created or deleted."""

    def __init__(self, runs: Path, run_id: str) -> None:
        super().__init__(run_id)
        self.runs = runs
        self.run_id = run_id


class LatestPointer(BaseModel):
    """The Story's `latest` pointer file: the run id of its newest Run."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    run_id: str


class RunFolders:
    """Creates the Run folders of the Stories in one working directory and points to the newest."""

    def __init__(
        self, working: WorkingDirectory, is_run_name: Callable[[str], bool], trash: Trash
    ) -> None:
        """`is_run_name` tells a Run folder's name from other names kept in `runs/`.

        Pruned Run folders go to `trash`, so a pruned Run can be restored.
        """
        self._stories = working.root / STORIES_FOLDER
        self._is_run_name = is_run_name
        self._trash = trash

    def create(self, story: str, run_id: str, runs_to_keep: int) -> RunFolder:
        """Create the Run folder, prune old runs so `runs_to_keep` remain, point `latest` at it.

        Touching nothing, raise `RefusedError` when the Story has no folder and
        `RunFolderTakenError` when the run id already has one.
        """
        story_folder = self._stories / story
        if not self._is_story_name(story) or not story_folder.is_dir():
            raise RefusedError(RefusalReason.NO_STORY, self._stories, story)
        runs = story_folder / RUNS_FOLDER
        path = runs / run_id
        try:
            path.mkdir(parents=True)
        except FileExistsError as error:
            raise RunFolderTakenError(runs, run_id) from error
        self._prune(runs, runs_to_keep)
        pointer = LatestPointer(run_id=run_id)
        JsonStore(story_folder / LATEST_POINTER_FILE, pointer).write(pointer)
        return RunFolder(run_id=run_id, path=path)

    @staticmethod
    def _is_story_name(story: str) -> bool:
        """Tell whether `story` names one folder right under `stories/`, never one outside it."""
        parts = Path(story).parts
        return len(parts) == STORY_NAME_PARTS and parts[0] != PARENT_FOLDER_NAME

    def _prune(self, runs: Path, keep: int) -> None:
        old = sorted((folder for folder in runs.iterdir() if self._is_run(folder)), reverse=True)
        for folder in old[keep:]:
            self._trash.trash(folder)

    def _is_run(self, folder: Path) -> bool:
        """Tell a Run folder from other things kept in `runs/`; pruning trashes only Run folders."""
        return folder.is_dir() and self._is_run_name(folder.name)

    @staticmethod
    @contextmanager
    def log(folder: RunFolder) -> Generator[TextIO]:
        """Open the Run's `run.log` for appending its JSON lines."""
        with (folder.path / RUN_LOG_FILE).open(APPEND_MODE, encoding=ENCODING) as handle:
            yield handle
