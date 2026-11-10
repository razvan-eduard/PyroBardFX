from pathlib import Path

import pytest
from pydantic import ValidationError

from pyrobardfx.domain.run_id import RunId
from pyrobardfx.run.snapshot import InvalidSnapshotError, RunSnapshot, RunSnapshotBuilder
from pyrobardfx.settings.constants import QualityPresetName
from pyrobardfx.settings.model import Settings
from pyrobardfx.settings.service import SettingsService
from pyrobardfx.workdir.working_directory import WorkingDirectory
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.clock import FakeClock

RUN_ID = RunId("20261109T153000Z-a1b2")


def test_a_snapshot_without_its_story_is_refused_naming_the_story() -> None:
    with pytest.raises(InvalidSnapshotError) as refused:
        RunSnapshotBuilder().run_id(RUN_ID).settings(Settings()).build()

    assert refused.value.fields == ("story",)


def test_a_snapshot_whose_run_id_is_not_shaped_like_one_is_refused_naming_the_run_id() -> None:
    with pytest.raises(InvalidSnapshotError) as refused:
        RunSnapshotBuilder().story("the-lighthouse").run_id(RunId("draft")).settings(
            Settings()
        ).build()

    assert refused.value.fields == ("run_id",)


def test_a_snapshot_read_back_from_its_json_holds_its_run_id_as_a_run_id() -> None:
    snapshot = RunSnapshotBuilder().story("the-lighthouse").run_id(RUN_ID).settings(Settings())

    read = RunSnapshot.model_validate_json(snapshot.build().model_dump_json())

    assert (type(read.run_id), read.run_id) == (RunId, RUN_ID)


def test_a_snapshot_without_its_run_id_is_refused_naming_the_run_id() -> None:
    with pytest.raises(InvalidSnapshotError) as refused:
        RunSnapshotBuilder().story("the-lighthouse").settings(Settings()).build()

    assert refused.value.fields == ("run_id",)


def test_a_snapshot_without_its_settings_is_refused_naming_the_settings() -> None:
    with pytest.raises(InvalidSnapshotError) as refused:
        RunSnapshotBuilder().story("the-lighthouse").run_id(RUN_ID).build()

    assert refused.value.fields == ("settings",)


def test_a_settings_edit_after_the_snapshot_is_built_leaves_the_snapshot_unchanged(
    tmp_path: Path,
) -> None:
    (tmp_path / "config").mkdir()
    settings = SettingsService.open(
        WorkingDirectory(root=tmp_path), FakeClock(), FanOutBuilder.over(FakeClock())
    )
    builder = RunSnapshotBuilder().story("the-lighthouse").run_id(RUN_ID)
    built = builder.settings(settings.read()).build()

    settings.write(Settings(runs_to_keep=9, quality_preset=QualityPresetName.BEST))

    assert built.settings == Settings()


def test_the_settings_of_a_built_snapshot_refuse_to_be_changed() -> None:
    builder = RunSnapshotBuilder().story("the-lighthouse").run_id(RUN_ID)
    built = builder.settings(Settings()).build()

    with pytest.raises(ValidationError):
        built.settings.runs_to_keep = 9  # ty: ignore[invalid-assignment]
