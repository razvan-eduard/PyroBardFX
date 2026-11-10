import pytest
from pydantic import ValidationError

from pyrobardfx.settings.constants import GLOBAL_SETTINGS
from pyrobardfx.settings.model import Settings


def test_settings_that_keep_no_runs_are_refused_naming_the_keep_count() -> None:
    with pytest.raises(ValidationError) as refused:
        Settings(runs_to_keep=0)

    assert [detail["loc"] for detail in refused.value.errors()] == [("runs_to_keep",)]


def test_each_global_setting_is_a_setting_of_the_model() -> None:
    assert Settings.model_fields.keys() >= GLOBAL_SETTINGS


def test_the_device_is_a_global_setting_as_it_belongs_to_the_machine() -> None:
    assert "device" in GLOBAL_SETTINGS
