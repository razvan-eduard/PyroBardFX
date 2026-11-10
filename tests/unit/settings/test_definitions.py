import json

import pytest
from pydantic import BaseModel, Field

from pyrobardfx.settings.constants import SettingGroup
from pyrobardfx.settings.definitions import SettingDefinition, SettingDefinitions
from pyrobardfx.settings.model import SettingMeta, Settings


def definition(name: str) -> SettingDefinition:
    return next(item for item in SettingDefinitions.of(Settings) if item.name == name)


def test_a_definition_carries_the_label_key_help_key_and_group_of_its_field() -> None:
    runs = definition("runs_to_keep")

    assert (runs.label_key, runs.help_key, runs.group) == (
        "settings.runs_to_keep.label",
        "settings.runs_to_keep.help",
        "runs",
    )


def test_a_definition_carries_the_kind_default_and_bounds_of_its_field() -> None:
    runs = definition("runs_to_keep")

    assert (runs.kind, runs.default, runs.minimum, runs.maximum) == ("integer", 5, 1, None)


def test_a_choice_definition_lists_its_choices_and_default() -> None:
    quality = definition("quality_preset")

    assert (quality.choices, quality.default) == (("fast", "balanced", "best"), "balanced")


def test_an_integer_bound_reaches_the_card_as_an_integer() -> None:
    card = json.loads(definition("runs_to_keep").model_dump_json())

    assert repr(card["minimum"]) == "1"


def test_the_ui_language_is_a_choice_of_the_five_languages_defaulting_to_english() -> None:
    ui = definition("ui_language")

    assert (ui.choices, ui.default) == (("ro", "en", "fr", "de", "es"), "en")


def test_the_ui_language_carries_its_label_key_help_key_and_the_language_group() -> None:
    ui = definition("ui_language")

    assert (ui.label_key, ui.help_key, ui.group) == (
        "settings.ui_language.label",
        "settings.ui_language.help",
        "language",
    )


def test_the_story_language_is_a_choice_of_the_five_languages_defaulting_to_english() -> None:
    story = definition("story_language")

    assert (story.choices, story.default) == (("ro", "en", "fr", "de", "es"), "en")


def test_the_story_language_carries_its_label_key_help_key_and_the_language_group() -> None:
    story = definition("story_language")

    assert (story.label_key, story.help_key, story.group) == (
        "settings.story_language.label",
        "settings.story_language.help",
        "language",
    )


def test_the_device_is_a_choice_of_auto_and_the_four_backends_defaulting_to_auto() -> None:
    device = definition("device")

    assert (device.choices, device.default) == (("auto", "mps", "mlx", "cuda", "cpu"), "auto")


def test_the_device_carries_its_label_key_help_key_and_the_device_group() -> None:
    device = definition("device")

    assert (device.label_key, device.help_key, device.group) == (
        "settings.device.label",
        "settings.device.help",
        "device",
    )


class _Volume(BaseModel):
    level: int = Field(
        default=3, gt=0, json_schema_extra=SettingMeta.of("l", "h", SettingGroup.RUNS)
    )


def test_a_constraint_a_definition_cannot_carry_is_refused_naming_its_setting() -> None:
    with pytest.raises(ValueError, match="level"):
        SettingDefinitions.of(_Volume)
