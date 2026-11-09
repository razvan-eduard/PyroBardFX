"""Run ids: a UTC timestamp plus a short random token."""

import re
from typing import Self

from pyrobardfx.clock.base import Clock
from pyrobardfx.run.constants import (
    RUN_ID_FORMAT,
    RUN_ID_PATTERN,
    RUN_ID_TIME_FORMAT,
    RUN_ID_TOKEN_BYTES,
)
from pyrobardfx.run.tokens import TokenSource


class RunId(str):
    """The name of one Run and its folder; run ids sort by the time their Run started."""

    __slots__ = ()

    @classmethod
    def draw(cls, clock: Clock, tokens: TokenSource) -> Self:
        """Return a new run id stamped with the clock's UTC time and a fresh token."""
        time = clock.utc_now().strftime(RUN_ID_TIME_FORMAT)
        return cls(RUN_ID_FORMAT.format(time=time, token=tokens.hex(RUN_ID_TOKEN_BYTES)))

    @staticmethod
    def matches(name: str) -> bool:
        """Tell whether `name` has the shape of a run id."""
        return re.fullmatch(RUN_ID_PATTERN, name) is not None
