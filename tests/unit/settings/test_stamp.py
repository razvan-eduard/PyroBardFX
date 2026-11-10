import pytest
from pydantic import JsonValue

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


def test_a_bool_value_is_written_as_json_and_parses_back_as_one_settings_tag() -> None:
    stamp = SettingsStamp(values={"quality_preset": "best", "draft": True})

    tags = ScriptParser().parse(stamp.restamped("# One\n")).global_tags

    assert [(tag.kind, tag.value) for tag in tags] == [
        (GlobalTagKind.SETTINGS, "quality_preset best, draft true")
    ]


def test_a_dict_value_is_written_as_compact_json_inside_the_one_settings_tag() -> None:
    stamp = SettingsStamp(values={"mix": {"bed": 0.5, "on": False}})

    tags = ScriptParser().parse(stamp.restamped("# One\n")).global_tags

    assert [(tag.kind, tag.value) for tag in tags] == [
        (GlobalTagKind.SETTINGS, 'mix {"bed":0.5,"on":false}')
    ]


@pytest.mark.parametrize(
    "value", [["fast", "best"], "a]b", "two\nlines", {"bands": [1, 2]}], ids=repr
)
def test_a_value_a_global_tag_cannot_hold_is_refused(value: JsonValue) -> None:
    with pytest.raises(ValueError, match="presets"):
        SettingsStamp(values={"presets": value}).tag()


def test_the_default_settings_add_no_stamp_to_a_script() -> None:
    script = "[TAGS-PRESENT]\n# One\n"

    assert SettingsStamp.of(Settings()).restamped(script) == script


def test_the_default_settings_take_the_script_stamp_out_and_leave_its_line() -> None:
    script = "[TAGS-PRESENT]\n  [settings: quality_preset fast]\n# One\n"

    assert SettingsStamp.of(Settings()).restamped(script) == "[TAGS-PRESENT]\n  \n# One\n"


def test_a_script_with_globals_markers_gets_a_new_stamp_inside_them() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))
    script = "[TAGS-PRESENT]\n[GLOBALS-START]\n[fx-all: grain 0.3]\n[GLOBALS-END]\n# One\n"

    assert stamp.restamped(script) == (
        "[TAGS-PRESENT]\n[GLOBALS-START]\n[settings: quality_preset best]\n"
        "[fx-all: grain 0.3]\n[GLOBALS-END]\n# One\n"
    )


def test_a_script_with_globals_markers_but_no_header_gets_the_stamp_inside_them() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    assert stamp.restamped("[GLOBALS-START]\n[GLOBALS-END]\n") == (
        "[GLOBALS-START]\n[settings: quality_preset best]\n[GLOBALS-END]\n"
    )


def test_a_tags_header_past_the_first_200_characters_is_no_header_to_stamp_after() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))
    script = "word " * 40 + "[TAGS-PRESENT]\n"

    assert stamp.restamped(script) == "[settings: quality_preset best]\n" + script


def test_a_crlf_script_with_globals_markers_gets_a_new_stamp_line_ending_crlf() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))
    script = "[TAGS-PRESENT]\r\n[GLOBALS-START]\r\n[GLOBALS-END]\r\n# One\r\n"

    assert stamp.restamped(script) == (
        "[TAGS-PRESENT]\r\n[GLOBALS-START]\r\n[settings: quality_preset best]\r\n"
        "[GLOBALS-END]\r\n# One\r\n"
    )


def test_a_crlf_script_gets_a_new_stamp_line_ending_crlf_after_its_tags_header() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    assert stamp.restamped("[TAGS-PRESENT]\r\n# One\r\n") == (
        "[TAGS-PRESENT]\r\n[settings: quality_preset best]\r\n# One\r\n"
    )


def test_a_crlf_script_without_an_anchor_gets_the_stamp_on_a_first_line_ending_crlf() -> None:
    stamp = SettingsStamp.of(Settings(quality_preset=QualityPresetName.BEST))

    assert stamp.restamped("# One\r\nA line.\r\n") == (
        "[settings: quality_preset best]\r\n# One\r\nA line.\r\n"
    )
