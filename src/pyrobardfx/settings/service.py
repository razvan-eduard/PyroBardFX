"""The settings service: the one writer of the settings and the setup presets."""

from collections.abc import Sequence
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, JsonValue

from pyrobardfx.clock.base import Clock
from pyrobardfx.events.constants import PERCENT_DONE
from pyrobardfx.events.fan_out import EventFanOut
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.settings.constants import (
    BACKUP_NAME,
    BACKUP_TIME_FORMAT,
    EVENT_SET_ASIDE,
    PRESETS_FILE,
    SETTINGS_FILE,
    STAGE_NAME,
)
from pyrobardfx.settings.model import Settings
from pyrobardfx.settings.presets import SetupPresetList, SetupPresetsFile
from pyrobardfx.settings.stamp import SettingsStamp
from pyrobardfx.store.constants import DUMP_MODE, EXTRA_FORBID
from pyrobardfx.store.json_store import JsonStore
from pyrobardfx.workdir.constants import CONFIG_FOLDER
from pyrobardfx.workdir.working_directory import WorkingDirectory


class SettingChange(BaseModel):
    """One setting a preset load changed, with its value before and after, as JSON values."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    name: str
    before: JsonValue
    after: JsonValue

    @classmethod
    def between(cls, before: Settings, after: Settings) -> tuple[Self, ...]:
        """Every setting whose value differs between `before` and `after`, in field order."""
        old, new = before.model_dump(mode=DUMP_MODE), after.model_dump(mode=DUMP_MODE)
        return tuple(
            cls(name=name, before=old[name], after=new[name])
            for name in new
            if old[name] != new[name]
        )


class SetAsideFile(BaseModel):
    """A broken store file the settings service moved aside at open, and where it went."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    path: Path
    backup: Path


class SettingsService:
    """Holds the settings and setup presets of one working directory; reads come from memory."""

    def __init__(
        self,
        settings: JsonStore[Settings],
        presets: JsonStore[SetupPresetsFile],
        set_aside: Sequence[SetAsideFile] = (),
    ) -> None:
        self._settings = settings
        self._presets = presets
        self._set_aside = tuple(set_aside)

    @classmethod
    def open(cls, working: WorkingDirectory, clock: Clock, events: EventFanOut) -> Self:
        """Load the settings of `working`; without a settings file, start from the default preset.

        A broken or invalid file is moved aside under a dated name, the start settings are loaded
        in its place and one event says where the file went. The service keeps a record of each
        file it set aside, in order, until `take_set_aside` hands them out.
        """
        opener = _StoreOpener(clock, events)
        config = working.root / CONFIG_FOLDER
        presets = opener.open(config / PRESETS_FILE, SetupPresetsFile())
        settings = opener.open(config / SETTINGS_FILE, presets.read().start_settings())
        return cls(settings, presets, opener.set_aside)

    def take_set_aside(self) -> tuple[SetAsideFile, ...]:
        """Return the records of the files set aside at open, in order; a later call gets none."""
        taken, self._set_aside = self._set_aside, ()
        return taken

    def read(self) -> Settings:
        return self._settings.read()

    def write(self, settings: Settings) -> None:
        self._settings.write(settings)

    def save_preset(self, name: str, *, overwrite: bool = False) -> None:
        """Save the settings that differ from the defaults as the setup preset `name`.

        Without `overwrite`, a name another setup preset holds is refused and the presets stay as
        they were. With it, that preset is replaced and stays the default if it was.
        """
        presets = self._presets.read()
        if not overwrite:
            self._refuse_taken(presets, name)
        self._presets.write(presets.saved(name, SettingsStamp.of(self.read())))

    def preset_diff(self, name: str) -> tuple[SettingChange, ...]:
        """Each setting a load of the setup preset `name` would change; nothing is written."""
        return SettingChange.between(self.read(), self._preset_settings(name))

    def load_preset(self, name: str) -> tuple[SettingChange, ...]:
        """Set the settings to the defaults with the fields of the setup preset `name` over them.

        Returns each setting the load changed, the same list `preset_diff` gave before it.
        """
        before, after = self.read(), self._preset_settings(name)
        self.write(after)
        return SettingChange.between(before, after)

    def presets(self) -> SetupPresetList:
        return self._presets.read().listed()

    def rename_preset(self, name: str, new_name: str) -> None:
        """Give the setup preset `name` the name `new_name`; a taken new name is refused."""
        presets = self._presets.read()
        self._refuse_unknown(presets, name)
        self._refuse_taken(presets, new_name)
        self._presets.write(presets.renamed(name, new_name))

    def delete_preset(self, name: str) -> None:
        """Remove the setup preset `name`; the settings stay as they are."""
        presets = self._presets.read()
        self._refuse_unknown(presets, name)
        self._presets.write(presets.deleted(name))

    def set_default_preset(self, name: str) -> None:
        """Make the setup preset `name` the default one."""
        presets = self._presets.read()
        self._refuse_unknown(presets, name)
        self._presets.write(presets.with_default(name))

    def _preset_settings(self, name: str) -> Settings:
        presets = self._presets.read()
        self._refuse_unknown(presets, name)
        return presets.settings_of(name)

    def _refuse_taken(self, presets: SetupPresetsFile, name: str) -> None:
        if name in presets.presets:
            raise RefusedError(RefusalReason.PRESET_NAME_TAKEN, self._presets.path, name)

    def _refuse_unknown(self, presets: SetupPresetsFile, name: str) -> None:
        if name not in presets.presets:
            raise RefusedError(RefusalReason.PRESET_UNKNOWN, self._presets.path, name)


class _StoreOpener:
    """Opens the store files of the settings area, setting a broken one aside with an event."""

    def __init__(self, clock: Clock, events: EventFanOut) -> None:
        self._clock = clock
        self._events = events.at(STAGE_NAME)
        self.set_aside: list[SetAsideFile] = []

    def open[M: BaseModel](self, path: Path, default: M) -> JsonStore[M]:
        time = self._clock.utc_now().strftime(BACKUP_TIME_FORMAT)
        backup = path.with_name(BACKUP_NAME.format(stem=path.stem, time=time, suffix=path.suffix))
        store, set_aside = JsonStore.open_or_set_aside(path, default, backup)
        if set_aside is not None:
            self.set_aside.append(SetAsideFile(path=path, backup=set_aside))
            self._events.emit(EVENT_SET_ASIDE, PERCENT_DONE, path=str(path), backup=str(set_aside))
        return store
