"""The setup presets file: named partial settings and the name of the default one."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from pyrobardfx.settings.constants import GLOBAL_SETTINGS, UNKNOWN_DEFAULT_MESSAGE
from pyrobardfx.settings.model import Settings
from pyrobardfx.settings.stamp import SettingsStamp
from pyrobardfx.store.constants import DUMP_MODE, EXTRA_FORBID, VALIDATE_AFTER


class SetupPresetList(BaseModel):
    """The names of the setup presets, sorted, and the name of the default one if any."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    names: tuple[str, ...]
    default: str | None


class SetupPresetsFile(BaseModel):
    """Each setup preset holds only the other settings it sets; the rest come from the defaults.

    A preset saved before the global settings left the presets may still hold some; they are
    checked with the rest, then ignored.
    """

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    default: str | None = None
    presets: dict[str, dict[str, JsonValue]] = Field(default_factory=dict)

    @model_validator(mode=VALIDATE_AFTER)
    def _each_preset_gives_valid_settings(self) -> Self:
        """Refuse a preset the settings refuse, and a default that names no preset."""
        for values in self.presets.values():
            Settings.model_validate(values)
        if self.default is not None and self.default not in self.presets:
            raise ValueError(UNKNOWN_DEFAULT_MESSAGE.format(name=self.default))
        return self

    def settings_of(self, name: str, current: Settings) -> Settings:
        """The settings the preset `name` gives over `current`.

        The other settings are the defaults with the preset's fields over them; the global
        settings stay those of `current`.
        """
        others = {
            key: value for key, value in self.presets[name].items() if key not in GLOBAL_SETTINGS
        }
        kept = current.model_dump(mode=DUMP_MODE, include=set(GLOBAL_SETTINGS))
        return Settings.model_validate({**others, **kept})

    def start_settings(self) -> Settings:
        """The settings a working directory starts from: the default preset's, else the defaults."""
        defaults = Settings()
        return defaults if self.default is None else self.settings_of(self.default, defaults)

    def saved(self, name: str, stamp: SettingsStamp) -> Self:
        """Return the file with the non-default fields of `stamp` saved as the preset `name`."""
        return type(self)(default=self.default, presets={**self.presets, name: stamp.values})

    def renamed(self, name: str, new_name: str) -> Self:
        """Return the file with the preset `name` under `new_name`; the default follows it."""
        presets = {new_name if key == name else key: values for key, values in self.presets.items()}
        default = new_name if self.default == name else self.default
        return type(self)(default=default, presets=presets)

    def deleted(self, name: str) -> Self:
        """Return the file without the preset `name`; deleting the default leaves no default."""
        presets = {key: values for key, values in self.presets.items() if key != name}
        return type(self)(default=None if self.default == name else self.default, presets=presets)

    def with_default(self, name: str) -> Self:
        """Return the file with `name` as the default preset."""
        return type(self)(default=name, presets=self.presets)

    def listed(self) -> SetupPresetList:
        return SetupPresetList(names=tuple(sorted(self.presets)), default=self.default)
