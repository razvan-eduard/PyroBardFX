"""Constants of the locales area."""

from enum import StrEnum
from pathlib import Path


class Language(StrEnum):
    """A language the app speaks; each value is the name of its folder under the locales folder."""

    RO = "ro"
    EN = "en"
    FR = "fr"
    DE = "de"
    ES = "es"


# The language whose text stands in for a key another language lacks.
FALLBACK_LANGUAGE = Language.EN
# The one place the code finds the locales folder: `locales/` at the repo root.
LOCALES_FOLDER = Path(__file__).parents[3] / "locales"
LOCALE_FILE = "main.json"
MISSING_LABEL_MESSAGE = (
    "the locale key {key} is missing from {language} and from the fallback {fallback}"
)
