from pyrobardfx.locales.constants import Language
from pyrobardfx.settings.constants import QualityPresetName
from pyrobardfx.settings.model import Settings
from pyrobardfx.settings.stamp import SettingsStamp


def test_a_stamp_lists_only_the_fields_that_differ_from_the_defaults() -> None:
    settings = Settings(runs_to_keep=5, quality_preset=QualityPresetName.BEST)

    assert SettingsStamp.of(settings).values == {"quality_preset": "best"}


def test_a_stamp_of_the_default_settings_is_empty() -> None:
    assert SettingsStamp.of(Settings()).values == {}


def test_a_stamp_holds_none_of_the_global_settings_even_when_they_differ_from_the_defaults() -> (
    None
):
    settings = Settings(
        runs_to_keep=9,
        quality_preset=QualityPresetName.BEST,
        ui_language=Language.RO,
        story_language=Language.FR,
    )

    assert SettingsStamp.of(settings).values == {"quality_preset": "best"}
