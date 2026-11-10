"""Builds a locales folder for a test, laid out as `src/pyrobardfx/locales/<lang>/main.json`."""

import json
import shutil
from pathlib import Path
from typing import Self

from pyrobardfx.locales.constants import LOCALE_FILE, LOCALES_FOLDER, Language


class LocalesBuilder:
    """Fluent builder of a locales folder; `build()` writes it and returns the folder."""

    def __init__(self, folder: Path) -> None:
        self._folder = folder
        self._texts: dict[Language, dict[str, str]] = {}
        self._real: list[Language] = []

    def texts(self, language: Language, texts: dict[str, str]) -> Self:
        """Give `language` a locale file holding only `texts`."""
        self._texts[language] = texts
        return self

    def real(self, language: Language) -> Self:
        """Give `language` a copy of the repo's own locale file."""
        self._real.append(language)
        return self

    def build(self) -> Path:
        for language in self._real:
            shutil.copytree(LOCALES_FOLDER / language, self._folder / language)
        for language, texts in self._texts.items():
            (self._folder / language).mkdir(parents=True)
            (self._folder / language / LOCALE_FILE).write_text(json.dumps(texts), encoding="utf-8")
        return self._folder
