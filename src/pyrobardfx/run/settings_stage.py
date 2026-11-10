"""The settings stage: names in the Run's events each settings file set aside at open."""

from pyrobardfx.domain.constants import StageName
from pyrobardfx.events.constants import PERCENT_DONE
from pyrobardfx.events.fan_out import StageEvents
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
        self, name: StageName, dependencies: StageDependencies, settings: SettingsService
    ) -> None:
        super().__init__(name, dependencies)
        self._settings = settings

    def body(self, inputs: RunFolder) -> RunFolder:
        self.replay(self._settings, self._events)
        return inputs

    @staticmethod
    def replay(settings: SettingsService, events: StageEvents) -> None:
        """Emit one set-aside event per record `settings` still holds; a record goes out once.

        A Run refused or cancelled before this stage calls it too, so its user still sees them.
        """
        for record in settings.take_set_aside():
            events.emit(
                EVENT_SET_ASIDE, PERCENT_DONE, path=str(record.path), backup=str(record.backup)
            )
