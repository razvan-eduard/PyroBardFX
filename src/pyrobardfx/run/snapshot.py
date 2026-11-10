"""The run snapshot: every value a Run reads, frozen at Run start (ADR 0002)."""

from typing import Self

from pydantic import BaseModel, ConfigDict, ValidationError

from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.domain.run_id import RunId
from pyrobardfx.run.constants import INVALID_SNAPSHOT_MESSAGE
from pyrobardfx.settings.model import Settings
from pyrobardfx.store.constants import ERROR_LOCATION_KEY, EXTRA_FORBID, LIST_JOINER


class RunSnapshot(BaseModel):
    """The frozen values one Run uses, handed to every stage and copied into its Run folder."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    story: str
    run_id: RunId
    settings: Settings
    backend_order: BackendOrder


class InvalidSnapshotError(Exception):
    """A snapshot builder was asked to build with a value unset or out of range."""

    def __init__(self, fields: tuple[str, ...]) -> None:
        super().__init__(INVALID_SNAPSHOT_MESSAGE.format(fields=LIST_JOINER.join(fields)))
        self.fields = fields


class RunSnapshotBuilder:
    """Collects the values of a run snapshot; `build()` refuses an incomplete or invalid one."""

    def __init__(self) -> None:
        self._story: str | None = None
        self._run_id: RunId | None = None
        self._settings: Settings | None = None
        self._backend_order: BackendOrder | None = None

    def story(self, name: str) -> Self:
        self._story = name
        return self

    def run_id(self, run_id: RunId) -> Self:
        self._run_id = run_id
        return self

    def settings(self, settings: Settings) -> Self:
        """Take the settings the Run reads; they are frozen, so a later edit never reaches it."""
        self._settings = settings
        return self

    def backend_order(self, order: BackendOrder) -> Self:
        """Take the backends every model of the Run may use, best first, resolved at its start."""
        self._backend_order = order
        return self

    def build(self) -> RunSnapshot:
        """Return the frozen snapshot, or raise `InvalidSnapshotError` naming the bad fields."""
        values = dict(
            story=self._story,
            run_id=self._run_id,
            settings=self._settings,
            backend_order=self._backend_order,
        )
        try:
            return RunSnapshot.model_validate(values)
        except ValidationError as error:
            fields = tuple(str(detail[ERROR_LOCATION_KEY][0]) for detail in error.errors())
            raise InvalidSnapshotError(fields) from error
