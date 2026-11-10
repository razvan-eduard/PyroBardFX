from pathlib import Path

import pytest
from pydantic import ValidationError

from pyrobardfx.run.snapshot import InvalidSnapshotError, RunSnapshotBuilder
from pyrobardfx.settings.constants import QualityPresetName
from pyrobardfx.settings.model import Settings
from pyrobardfx.settings.service import SettingsService
from pyrobardfx.workdir.working_directory import WorkingDirectory
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.clock import FakeClock


def test_a_snapshot_without_its_run_id_is_refused_naming_the_run_id() -> None:
    with pytest.raises(InvalidSnapshotError) as refused:
        RunSnapshotBuilder().story("the-lighthouse").settings(Settings()).build()

    assert refused.value.fields == ("run_id",)


def test_a_snapshot_without_its_settings_is_refused_naming_the_settings() -> None:
    with pytest.raises(InvalidSnapshotError) as refused:
        RunSnapshotBuilder().story("the-lighthouse").run_id("20261109T153000Z-a1b2").build()

    assert refused.value.fields == ("settings",)


def test_a_settings_edit_after_the_snapshot_is_built_leaves_the_snapshot_unchanged(
    tmp_path: Path,
) -> None:
    (tmp_path / "config").mkdir()
    settings = SettingsService.open(
        WorkingDirectory(root=tmp_path), FakeClock(), FanOutBuilder.over(FakeClock())
    )
    builder = RunSnapshotBuilder().story("the-lighthouse").run_id("20261109T153000Z-a1b2")
    built = builder.settings(settings.read()).build()

    settings.write(Settings(runs_to_keep=9, quality_preset=QualityPresetName.BEST))

    assert built.settings == Settings()


def test_the_settings_of_a_built_snapshot_refuse_to_be_changed() -> None:
    builder = RunSnapshotBuilder().story("the-lighthouse").run_id("20261109T153000Z-a1b2")
    built = builder.settings(Settings()).build()

    with pytest.raises(ValidationError):
        built.settings.runs_to_keep = 9  # ty: ignore[invalid-assignment]
