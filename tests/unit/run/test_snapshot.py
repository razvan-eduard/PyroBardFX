import pytest

from pyrobardfx.run.snapshot import InvalidSnapshotError, RunSnapshotBuilder


def test_a_snapshot_without_its_run_id_is_refused_naming_the_run_id() -> None:
    with pytest.raises(InvalidSnapshotError) as refused:
        RunSnapshotBuilder().story("the-lighthouse").build()

    assert refused.value.fields == ("run_id",)


def test_a_snapshot_that_keeps_no_runs_is_refused_naming_the_keep_count() -> None:
    builder = RunSnapshotBuilder().story("the-lighthouse").run_id("20261109T153000Z-a1b2")

    with pytest.raises(InvalidSnapshotError) as refused:
        builder.runs_to_keep(0).build()

    assert refused.value.fields == ("runs_to_keep",)
