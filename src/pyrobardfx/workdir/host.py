"""The facts about the host that decide where the working directory goes."""

import os
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pyrobardfx.workdir.constants import FIXED_TEMP_ROOTS


@dataclass(frozen=True)
class HostFacts:
    """A snapshot of the host, read once at start so nothing after it reads the process state."""

    platform: str
    home: Path
    environ: Mapping[str, str]
    system_temp: Path
    fixed_temp_roots: tuple[Path, ...]

    @classmethod
    def from_host(cls) -> Self:
        return cls(
            platform=sys.platform,
            home=Path.home(),
            environ=dict(os.environ),
            system_temp=Path(tempfile.gettempdir()),
            fixed_temp_roots=FIXED_TEMP_ROOTS,
        )
