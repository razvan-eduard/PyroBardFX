from pathlib import Path

import pytest

from pyrobardfx.locales.constants import Language
from pyrobardfx.locales.labels import Labels, MissingLabelError
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

    with pytest.raises(MissingLabelError):
        Labels.load(Language.RO, folder).label(FINISHED)


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
