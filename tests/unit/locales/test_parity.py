import json
import pkgutil
from importlib import import_module
from pathlib import Path
from string import Formatter
from types import ModuleType

import pytest

import pyrobardfx
from pyrobardfx.locales.constants import LOCALE_FILE, LOCALES_FOLDER, Language
from pyrobardfx.refusal.constants import RefusalReason
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


def test_every_key_of_the_locale_files_is_used_by_the_code() -> None:
    source = "".join(path.read_text(encoding="utf-8") for path in SOURCE.rglob("*.py"))

    assert {key for key in every_key() if f'"{key}"' not in source} == set()


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
