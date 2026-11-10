"""The run snapshot: every value a Run reads, frozen at Run start (ADR 0002)."""

from typing import Self

from pydantic import BaseModel, ConfigDict, ValidationError

from pyrobardfx.run.constants import ERROR_LOCATION_KEY, FIELD_SEPARATOR, INVALID_SNAPSHOT_MESSAGE
from pyrobardfx.settings.model import Settings
from pyrobardfx.store.constants import EXTRA_FORBID


class RunSnapshot(BaseModel):
    """The frozen values one Run uses, handed to every stage and copied into its Run folder."""

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    story: str
    run_id: str
    settings: Settings


class InvalidSnapshotError(Exception):
    """A snapshot builder was asked to build with a value unset or out of range."""

    def __init__(self, fields: tuple[str, ...]) -> None:
        super().__init__(INVALID_SNAPSHOT_MESSAGE.format(fields=FIELD_SEPARATOR.join(fields)))
        self.fields = fields


class RunSnapshotBuilder:
    """Collects the values of a run snapshot; `build()` refuses an incomplete or invalid one."""

    def __init__(self) -> None:
        self._story: str | None = None
        self._run_id: str | None = None
        self._settings: Settings | None = None

    def story(self, name: str) -> Self:
        self._story = name
        return self

    def run_id(self, run_id: str) -> Self:
        self._run_id = run_id
        return self

    def settings(self, settings: Settings) -> Self:
        """Take the settings the Run reads; they are frozen, so a later edit never reaches it."""
        self._settings = settings
        return self

    def build(self) -> RunSnapshot:
        """Return the frozen snapshot, or raise `InvalidSnapshotError` naming the bad fields."""
        values = dict(story=self._story, run_id=self._run_id, settings=self._settings)
        try:
            return RunSnapshot.model_validate(values)
        except ValidationError as error:
            fields = tuple(str(detail[ERROR_LOCATION_KEY][0]) for detail in error.errors())
            raise InvalidSnapshotError(fields) from error
