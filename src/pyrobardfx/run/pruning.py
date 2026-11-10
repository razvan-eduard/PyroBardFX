"""The pruning stage: the first stage of a Run, trashing old Runs down to the keep count."""

from pyrobardfx.run.stage import Stage, StageDependencies
from pyrobardfx.workdir.run_folders import RunFolder, RunFolders


class PruneRunsStage(Stage[RunFolder, RunFolder]):
    """Trashes the oldest Run folders beside the new one so `runs_to_keep` remain.

    As a stage it passes a cancel check first, so a Run cancelled at once trashes nothing.
    """

    def __init__(self, name: str, dependencies: StageDependencies, folders: RunFolders) -> None:
        super().__init__(name, dependencies)
        self._folders = folders

    def body(self, inputs: RunFolder) -> RunFolder:
        self._folders.prune(inputs, self.snapshot.settings.runs_to_keep, self._events)
        return inputs
