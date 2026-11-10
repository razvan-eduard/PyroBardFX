"""The labels of one language: every user-facing text, looked up by its key."""

from collections.abc import Mapping
from pathlib import Path
from typing import Self

from pydantic import RootModel

from pyrobardfx.locales.constants import (
    FALLBACK_LANGUAGE,
    LOCALE_FILE,
    LOCALES_FOLDER,
    MISSING_FALLBACK_LOCALE_MESSAGE,
    MISSING_LABEL_MESSAGE,
    Language,
)
from pyrobardfx.store.json_store import JsonStore


class LocaleFile(RootModel[dict[str, str]]):
    """One `<lang>/main.json`: the text of each locale key in that language."""


class MissingLabelError(LookupError):
    """A key is in neither the language's locale file nor the fallback's: a defect in the code."""


class MissingFallbackLocaleError(FileNotFoundError):
    """The fallback's own locale file is absent, so no label could stand in: a broken install."""


class Labels:
    """The text of one language from `<folder>/<lang>/main.json`; a key it lacks falls back to en.

    No id, event name, tag or file name is looked up here: those stay English (story 18).
    """

    def __init__(
        self,
        language: Language,
        folder: Path,
        texts: Mapping[str, str],
        fallback: Mapping[str, str],
    ) -> None:
        self._language = language
        self._folder = folder
        self._texts = texts
        self._fallback = fallback

    @classmethod
    def load(cls, language: Language, folder: Path = LOCALES_FOLDER) -> Self:
        """Read the locale files of `language` and of the fallback from `folder`.

        A missing fallback file raises `MissingFallbackLocaleError` here, before any lookup.
        """
        fallback = cls._read_fallback(folder)
        texts = fallback if language == FALLBACK_LANGUAGE else cls._read(folder, language)
        return cls(language, folder, texts, fallback)

    def for_language(self, language: Language) -> Self:
        """Return the labels of `language`, read from this one's locales folder."""
        return self.load(language, self._folder)

    def label(self, key: str) -> str:
        """Return the text of `key`; a key missing in en too raises `MissingLabelError`."""
        text = self._texts.get(key, self._fallback.get(key))
        if text is None:
            raise MissingLabelError(
                MISSING_LABEL_MESSAGE.format(
                    key=key, language=self._language, fallback=FALLBACK_LANGUAGE
                )
            )
        return text

    @classmethod
    def _read_fallback(cls, folder: Path) -> dict[str, str]:
        """The texts of the fallback; unlike any other language, it must have its locale file."""
        path = folder / FALLBACK_LANGUAGE / LOCALE_FILE
        if not path.exists():
            raise MissingFallbackLocaleError(MISSING_FALLBACK_LOCALE_MESSAGE.format(path=path))
        return cls._read(folder, FALLBACK_LANGUAGE)

    @staticmethod
    def _read(folder: Path, language: Language) -> dict[str, str]:
        """The texts of `language`; a language with no locale file has none of its own."""
        return JsonStore.open(folder / language / LOCALE_FILE, LocaleFile({})).read().root
