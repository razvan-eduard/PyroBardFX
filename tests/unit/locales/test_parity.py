import json
import pkgutil
from importlib import import_module
from pathlib import Path
from string import Formatter
from types import ModuleType

import pytest

import pyrobardfx
from pyrobardfx.content_types.constants import DATA_FILE_PATTERN, SHIPPED_FOLDER
from pyrobardfx.locales.constants import LOCALE_FILE, LOCALES_FOLDER, Language
from pyrobardfx.refusal.constants import (
    FIXED_PLACEHOLDERS,
    FURTHER_PLACEHOLDERS,
    RefusalReason,
)
from pyrobardfx.settings.definitions import SettingDefinitions
from pyrobardfx.settings.model import Settings

SOURCE = Path(__file__).parents[3] / "src" / "pyrobardfx"
LABEL_KEY_SUFFIX = "_LABEL_KEY"
CONSTANTS_MODULE = ".constants"


def texts_of(language: Language) -> dict[str, str]:
    return json.loads((LOCALES_FOLDER / language / LOCALE_FILE).read_text(encoding="utf-8"))


def constants_modules() -> list[ModuleType]:
    """Every `pyrobardfx.*.constants` module, found by walking the package."""
    return [
        import_module(info.name)
        for info in pkgutil.walk_packages(pyrobardfx.__path__, f"{pyrobardfx.__name__}.")
        if info.name.endswith(CONSTANTS_MODULE)
    ]


def shipped_content_type_label_keys() -> set[str]:
    """The `label_key` of each shipped Content type data file."""
    return {
        json.loads(path.read_text(encoding="utf-8"))["label_key"]
        for path in SHIPPED_FOLDER.glob(DATA_FILE_PATTERN)
    }


def every_key() -> set[str]:
    return {key for language in Language for key in texts_of(language)}


def placeholders_of(text: str) -> list[tuple[str, str]]:
    """Each `{name:spec}` of `text` as `(name, spec)`, sorted: word order may move them."""
    return sorted(
        (name, spec or "") for _, name, spec, _ in Formatter().parse(text) if name is not None
    )


@pytest.mark.parametrize("language", list(Language))
def test_each_locale_file_holds_every_key_any_locale_file_holds(language: Language) -> None:
    assert every_key() - texts_of(language).keys() == set()


@pytest.mark.parametrize("language", list(Language))
def test_each_translation_keeps_the_placeholders_of_the_english_text(language: Language) -> None:
    english = texts_of(Language.EN)
    changed = {
        key
        for key, text in texts_of(language).items()
        if placeholders_of(text) != placeholders_of(english.get(key, ""))
    }

    assert changed == set()


def test_every_placeholder_of_a_refusal_text_is_one_its_refusal_gives_a_value() -> None:
    english = texts_of(Language.EN)
    unfilled = {
        reason: names
        for reason in RefusalReason
        if (
            names := {name for name, _ in placeholders_of(english[reason])}
            - FIXED_PLACEHOLDERS
            - FURTHER_PLACEHOLDERS.get(reason, frozenset())
        )
    }

    assert unfilled == {}


def test_every_key_of_the_locale_files_is_used_by_the_code() -> None:
    source = "".join(path.read_text(encoding="utf-8") for path in SOURCE.rglob("*.py"))
    unused = {key for key in every_key() if f'"{key}"' not in source}

    assert unused - shipped_content_type_label_keys() == set()


def test_the_english_locale_holds_every_refusal_and_settings_key_of_the_code() -> None:
    settings = {
        key for item in SettingDefinitions.of(Settings) for key in (item.label_key, item.help_key)
    }

    assert (settings | set(RefusalReason)) - texts_of(Language.EN).keys() == set()


def test_the_english_locale_holds_every_locale_key_of_every_constants_module() -> None:
    modules = constants_modules()
    keys = {
        value
        for module in modules
        for name, value in vars(module).items()
        if name.endswith(LABEL_KEY_SUFFIX)
    }

    assert {"cli", "events", "adapters"} <= {module.__name__.split(".")[1] for module in modules}
    assert keys - texts_of(Language.EN).keys() == set()


def test_the_english_locale_holds_the_label_key_of_each_shipped_content_type() -> None:
    keys = shipped_content_type_label_keys()

    assert len(keys) == len(list(SHIPPED_FOLDER.glob(DATA_FILE_PATTERN)))
    assert keys - texts_of(Language.EN).keys() == set()
