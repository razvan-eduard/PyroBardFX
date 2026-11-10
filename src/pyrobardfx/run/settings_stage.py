"""The settings stage: names in the Run's events each settings file set aside at open."""

from pyrobardfx.events.constants import PERCENT_DONE
from pyrobardfx.run.stage import Stage, StageDependencies
from pyrobardfx.settings.constants import EVENT_SET_ASIDE
from pyrobardfx.settings.service import SettingsService
from pyrobardfx.workdir.run_folders import RunFolder


class SettingsStage(Stage[RunFolder, RunFolder]):
    """Replays one set-aside event per file the settings service set aside, so `run.log` has it.

    The service hands its records out once: a later Run on the same service replays none. The
    stage reads no settings file; the snapshot was built from the settings before the Run began.
    """

    def __init__(
        self, name: str, dependencies: StageDependencies, settings: SettingsService
    ) -> None:
        super().__init__(name, dependencies)
        self._settings = settings

    def body(self, inputs: RunFolder) -> RunFolder:
        for record in self._settings.take_set_aside():
            self._events.emit(
                EVENT_SET_ASIDE, PERCENT_DONE, path=str(record.path), backup=str(record.backup)
            )
        return inputs
