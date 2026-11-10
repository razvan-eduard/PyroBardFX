import json
from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from pyrobardfx.settings.constants import SettingGroup
from pyrobardfx.settings.definitions import SettingDefinition, SettingDefinitions
from pyrobardfx.settings.model import SettingMeta, Settings

ENGLISH_LOCALE = Path(__file__).parents[3] / "locales" / "en" / "main.json"


def definition(name: str) -> SettingDefinition:
    return next(item for item in SettingDefinitions.of(Settings) if item.name == name)


def test_the_english_locale_holds_every_label_and_help_key_of_the_settings() -> None:
    english = json.loads(ENGLISH_LOCALE.read_text(encoding="utf-8"))
    definitions = SettingDefinitions.of(Settings)
    keys = {key for item in definitions for key in (item.label_key, item.help_key)}

    assert keys - english.keys() == set()


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


class _Volume(BaseModel):
    level: int = Field(
        default=3, gt=0, json_schema_extra=SettingMeta.of("l", "h", SettingGroup.RUNS)
    )


def test_a_constraint_a_definition_cannot_carry_is_refused_naming_its_setting() -> None:
    with pytest.raises(ValueError, match="level"):
        SettingDefinitions.of(_Volume)
