"""Run ids: a UTC timestamp plus a short random token."""

import re
from typing import Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from pyrobardfx.clock.base import Clock
from pyrobardfx.clock.constants import UTC_NAME_TIME_FORMAT
from pyrobardfx.domain.constants import (
    NOT_A_RUN_ID_MESSAGE,
    RUN_ID_FORMAT,
    RUN_ID_PATTERN,
    RUN_ID_TOKEN_BYTES,
)
from pyrobardfx.domain.tokens import TokenSource


class RunId(str):
    """The name of one Run and its folder; run ids sort by the time their Run started."""

    __slots__ = ()

    @classmethod
    def draw(cls, clock: Clock, tokens: TokenSource) -> Self:
        """Return a new run id stamped with the clock's UTC time and a fresh token."""
        time = clock.utc_now().strftime(UTC_NAME_TIME_FORMAT)
        return cls(RUN_ID_FORMAT.format(time=time, token=tokens.hex(RUN_ID_TOKEN_BYTES)))

    @staticmethod
    def matches(name: str) -> bool:
        """Tell whether `name` has the shape of a run id."""
        return re.fullmatch(RUN_ID_PATTERN, name) is not None

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: object, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Read a run id from its plain string, refusing other shapes; write it back as one."""
        return core_schema.no_info_after_validator_function(cls._parse, core_schema.str_schema())

    @classmethod
    def _parse(cls, name: str) -> Self:
        if not cls.matches(name):
            raise ValueError(NOT_A_RUN_ID_MESSAGE.format(name=name))
        return cls(name)
