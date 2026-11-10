"""Constants of the locales area."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType


class Language(StrEnum):
    """A language the app speaks; each value is the name of its folder under the locales folder."""

    RO = "ro"
    EN = "en"
    FR = "fr"
    DE = "de"
    ES = "es"


# The language whose text stands in for a key another language lacks.
FALLBACK_LANGUAGE = Language.EN
# The one place the code finds the locales folder: this package's own folder,
# `src/pyrobardfx/locales/`, so a checkout and an installed wheel find the same files.
LOCALES_FOLDER = Path(__file__).parent
LOCALE_FILE = "main.json"
MISSING_LABEL_MESSAGE = (
    "the locale key {key} is missing from {language} and from the fallback {fallback}"
)


@dataclass(frozen=True)
class StorySpeech:
    """How a Story in one language is heard: transcription (ticket 08) and voice (ticket 09)."""

    # The ISO 639-1 code Whisper takes as its `language`.
    whisper_language: str
    # The BCP 47 language-region locale that picks the TTS voice.
    voice_locale: str


# The speech of each story language; the story language setting picks the entry.
STORY_SPEECH: Mapping[Language, StorySpeech] = MappingProxyType(
    {
        Language.RO: StorySpeech(whisper_language="ro", voice_locale="ro-RO"),
        Language.EN: StorySpeech(whisper_language="en", voice_locale="en-US"),
        Language.FR: StorySpeech(whisper_language="fr", voice_locale="fr-FR"),
        Language.DE: StorySpeech(whisper_language="de", voice_locale="de-DE"),
        Language.ES: StorySpeech(whisper_language="es", voice_locale="es-ES"),
    }
)
