"""Builds the host facts a test start sees, every path inside the test's sandbox folder."""

from pathlib import Path
from typing import Self

from pyrobardfx.workdir.host import HostFacts


class HostFactsBuilder:
    """Fluent builder for `HostFacts`; defaults to a macOS host with an empty environment."""

    def __init__(self, sandbox: Path) -> None:
        self._platform = "darwin"
        self._home = sandbox / "home"
        self._environ: dict[str, str] = {}
        self._system_temp = sandbox / "system-temp"
        self._fixed_temp_roots = (sandbox / "fixed-temp",)

    def platform(self, name: str) -> Self:
        self._platform = name
        return self

    def env(self, key: str, value: str) -> Self:
        self._environ[key] = value
        return self

    def build(self) -> HostFacts:
        return HostFacts(
            platform=self._platform,
            home=self._home,
            environ=dict(self._environ),
            system_temp=self._system_temp,
            fixed_temp_roots=self._fixed_temp_roots,
        )
