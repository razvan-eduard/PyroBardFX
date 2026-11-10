from pyrobardfx.domain.constants import StageName
from pyrobardfx.run.constants import STAGE_ORDER


def test_every_stage_name_is_passed_once_pruning_first_then_in_the_harness_order() -> None:
    assert list(StageName) == [StageName.PRUNE_RUNS, *STAGE_ORDER]
