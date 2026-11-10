"""The fake stage: adds its name to the names it is given, with a cancel check in its body."""

from pyrobardfx.run.stage import Stage, StageDependencies

# How far into the fake stage its cancel check sits, between its two steps.
CHECK_PERCENT = 50.0


class FakeStage(Stage[tuple[str, ...], tuple[str, ...]]):
    """Does two steps with a cancel check between them, keeping the steps it did in `done`.

    It returns the names it was given with its own name added, so a test can see the order.
    """

    def __init__(self, name: str, dependencies: StageDependencies) -> None:
        super().__init__(name, dependencies)
        self.done: list[str] = []

    def body(self, inputs: tuple[str, ...]) -> tuple[str, ...]:
        self.done.append("first")
        self.check_cancel(CHECK_PERCENT)
        self.done.append("second")
        return (*inputs, self.name)
