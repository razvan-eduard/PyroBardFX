"""The stages of a Run, in the order a Run passes them."""

from structlog.typing import FilteringBoundLogger

from pyrobardfx.clock.base import Clock
from pyrobardfx.run.constants import STAGE_ORDER
from pyrobardfx.run.snapshot import RunSnapshot
from pyrobardfx.run.stage import Stage


class NoOpStage(Stage):
    """Stands in for a stage not built yet, so a Run still passes through its place."""

    def body(self) -> None:
        return None


class Pipeline:
    """Makes the stages of one Run over its snapshot."""

    @staticmethod
    def stages(snapshot: RunSnapshot, log: FilteringBoundLogger, clock: Clock) -> tuple[Stage, ...]:
        return tuple(NoOpStage(name, snapshot, log, clock) for name in STAGE_ORDER)
