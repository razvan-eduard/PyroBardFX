"""Builds a laid-out working directory with Stories and Run folders for a test."""

from pathlib import Path
from typing import Self

from pyrobardfx.settings.model import Settings


class WorkingDirectoryBuilder:
    """Fluent builder of a working directory on disk; `build()` writes it and returns its root."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._stories: list[str] = []
        self._run_folders: list[tuple[str, str]] = []
        self._settings: Settings | None = None

    def story(self, name: str) -> Self:
        self._stories.append(name)
        return self

    def run_folder(self, story: str, name: str) -> Self:
        self._run_folders.append((story, name))
        return self

    def settings(self, settings: Settings) -> Self:
        """Write `settings` as the settings file, as a creator's earlier edit would have."""
        self._settings = settings
        return self

    def build(self) -> Path:
        if self._settings is not None:
            (self._root / "config").mkdir(parents=True, exist_ok=True)
            (self._root / "config" / "settings.json").write_text(self._settings.model_dump_json())
        for name in self._stories:
            (self._root / "stories" / name).mkdir(parents=True, exist_ok=True)
        for story, name in self._run_folders:
            (self._root / "stories" / story / "runs" / name).mkdir(parents=True, exist_ok=True)
        return self._root
