"""The stages of a Run, in the order a Run passes them."""

from collections.abc import Sequence
from typing import Self

from pyrobardfx.run.constants import STAGE_ORDER
from pyrobardfx.run.stage import Stage, StageDependencies


class NoOpStage[Value](Stage[Value, Value]):
    """Stands in for a stage not built yet: a Run passes its place with its value unchanged."""

    def body(self, inputs: Value) -> Value:
        return inputs


class Pipeline[Value]:
    """The stages of one Run in order; each stage takes the value the stage before returned."""

    def __init__(self, stages: Sequence[Stage[Value, Value]]) -> None:
        self._stages = tuple(stages)

    @classmethod
    def harness(cls, dependencies: StageDependencies, *stages: Stage[Value, Value]) -> Self:
        """Return `stages` placed into the harness order, each name without a stage a no-op.

        A stage named in `STAGE_ORDER` takes the place of that name's no-op; the other `stages`
        run first, in the order given.
        """
        built = {stage.name: stage for stage in stages if stage.name in STAGE_ORDER}
        first = (stage for stage in stages if stage.name not in STAGE_ORDER)
        harness = (built.get(name) or NoOpStage[Value](name, dependencies) for name in STAGE_ORDER)
        return cls((*first, *harness))

    def run(self, value: Value) -> Value:
        """Pass `value` through every stage in order and return what the last stage returned."""
        for stage in self._stages:
            value = stage.run(value)
        return value
