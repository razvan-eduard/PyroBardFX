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
    def harness(cls, dependencies: StageDependencies, *first: Stage[Value, Value]) -> Self:
        """Return the `first` stages, then the harness order, each a no-op until its ticket."""
        harness = (NoOpStage[Value](name, dependencies) for name in STAGE_ORDER)
        return cls((*first, *harness))

    def run(self, value: Value) -> Value:
        """Pass `value` through every stage in order and return what the last stage returned."""
        for stage in self._stages:
            value = stage.run(value)
        return value
