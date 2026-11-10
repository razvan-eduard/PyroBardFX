from pyrobardfx.locales.constants import Language
from pyrobardfx.script.constants import GlobalTagKind
from pyrobardfx.script.parser import ScriptParser
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


def test_a_stamp_is_written_as_a_settings_tag_naming_each_value() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    assert stamp.tag() == "[settings: quality_preset best]"


def test_a_re_stamp_replaces_the_script_stamp_and_leaves_every_other_byte_as_written() -> None:
    script = "[TAGS-PRESENT]\n[settings: quality_preset fast]  \n# One\n\n\tA door [sfx: door]. \n"
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    assert stamp.restamped(script) == (
        "[TAGS-PRESENT]\n[settings: quality_preset best]  \n# One\n\n\tA door [sfx: door]. \n"
    )


def test_a_script_without_a_stamp_gets_it_on_its_own_line_after_the_tags_header() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    assert stamp.restamped("[TAGS-PRESENT]\n# One\n") == (
        "[TAGS-PRESENT]\n[settings: quality_preset best]\n# One\n"
    )


def test_a_script_without_a_stamp_or_a_tags_header_gets_the_stamp_on_its_first_line() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    assert stamp.restamped("# One\n") == "[settings: quality_preset best]\n# One\n"


def test_a_written_stamp_parses_as_the_script_settings_tag_holding_its_values() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    tags = ScriptParser().parse(stamp.restamped("# One\n")).global_tags

    assert [(tag.kind, tag.value) for tag in tags] == [
        (GlobalTagKind.SETTINGS, "quality_preset best")
    ]
