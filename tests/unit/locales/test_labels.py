from pathlib import Path

import pytest

from pyrobardfx.locales.constants import (
    LOCALE_FILE,
    MISSING_FALLBACK_LOCALE_MESSAGE,
    MISSING_LABEL_MESSAGE,
    Language,
)
from pyrobardfx.locales.labels import Labels, MissingFallbackLocaleError, MissingLabelError
from tests.builders.locales import LocalesBuilder

FINISHED = "run.finished"


def test_a_label_is_the_text_of_its_key_in_the_given_language(tmp_path: Path) -> None:
    folder = (
        LocalesBuilder(tmp_path)
        .texts(Language.EN, {FINISHED: "Finished"})
        .texts(Language.RO, {FINISHED: "Gata"})
        .build()
    )

    assert Labels.load(Language.RO, folder).label(FINISHED) == "Gata"


def test_a_key_missing_in_the_given_language_falls_back_to_english(tmp_path: Path) -> None:
    folder = (
        LocalesBuilder(tmp_path)
        .texts(Language.EN, {FINISHED: "Finished"})
        .texts(Language.RO, {})
        .build()
    )

    assert Labels.load(Language.RO, folder).label(FINISHED) == "Finished"


def test_a_key_missing_in_english_too_is_reported_as_a_missing_label(tmp_path: Path) -> None:
    folder = LocalesBuilder(tmp_path).texts(Language.EN, {}).texts(Language.RO, {}).build()

    labels = Labels.load(Language.RO, folder)

    with pytest.raises(MissingLabelError) as raised:
        labels.label(FINISHED)
    assert str(raised.value) == MISSING_LABEL_MESSAGE.format(
        key=FINISHED, language=Language.RO, fallback=Language.EN
    )


def test_labels_for_another_language_read_that_language_from_the_same_folder(
    tmp_path: Path,
) -> None:
    folder = (
        LocalesBuilder(tmp_path)
        .texts(Language.EN, {FINISHED: "Finished"})
        .texts(Language.RO, {FINISHED: "Gata"})
        .build()
    )

    assert Labels.load(Language.RO, folder).for_language(Language.EN).label(FINISHED) == (
        "Finished"
    )


def test_a_language_without_a_locale_file_falls_back_to_english(tmp_path: Path) -> None:
    folder = LocalesBuilder(tmp_path).texts(Language.EN, {FINISHED: "Finished"}).build()

    assert Labels.load(Language.RO, folder).label(FINISHED) == "Finished"


@pytest.mark.parametrize("language", list(Language))
def test_a_folder_without_an_english_locale_file_fails_at_load_naming_that_file(
    tmp_path: Path, language: Language
) -> None:
    folder = LocalesBuilder(tmp_path).texts(Language.RO, {FINISHED: "Gata"}).build()

    with pytest.raises(MissingFallbackLocaleError) as raised:
        Labels.load(language, folder)
    assert str(raised.value) == MISSING_FALLBACK_LOCALE_MESSAGE.format(
        path=folder / Language.EN / LOCALE_FILE
    )
