import pytest
from pydantic import ValidationError

from pyrobardfx.settings.model import Settings


def test_settings_that_keep_no_runs_are_refused_naming_the_keep_count() -> None:
    with pytest.raises(ValidationError) as refused:
        Settings(runs_to_keep=0)

    assert [detail["loc"] for detail in refused.value.errors()] == [("runs_to_keep",)]
