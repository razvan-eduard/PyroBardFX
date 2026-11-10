from pathlib import Path

import pytest

from pyrobardfx.content_types.catalogue import ContentTypes
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.workdir.constants import CONTENT_TYPES_FOLDER
from pyrobardfx.workdir.working_directory import WorkingDirectory
from tests.fakes.content_type_detector import AnsweringDetector

SCRIPT = "The house at the end of the lane had been empty for years."


def shipped(root: Path) -> ContentTypes:
    return ContentTypes.load(WorkingDirectory(root=root))


def test_a_named_content_type_is_taken_without_asking_the_model(tmp_path: Path) -> None:
    detector = AnsweringDetector("scary story")

    picked = shipped(tmp_path).resolve("book_chapter", SCRIPT, detector)

    assert (picked, detector.asked) == ("book_chapter", [])


def test_auto_takes_the_content_type_the_model_answer_names(tmp_path: Path) -> None:
    detector = AnsweringDetector("This reads as a Scary Story.")

    assert shipped(tmp_path).resolve("auto", SCRIPT, detector) == "scary_story"


def test_auto_offers_the_model_the_script_and_every_content_type_name(tmp_path: Path) -> None:
    detector = AnsweringDetector("scary story")

    shipped(tmp_path).resolve("auto", SCRIPT, detector)

    assert detector.asked == [(SCRIPT, ("book_chapter", "drug_story", "scary_story"))]


def test_auto_takes_the_content_type_whose_first_word_the_answer_holds(tmp_path: Path) -> None:
    detector = AnsweringDetector("Book.")

    assert shipped(tmp_path).resolve("auto", SCRIPT, detector) == "book_chapter"


def refusal_of(content_types: ContentTypes, choice: str, detector: AnsweringDetector) -> tuple:
    with pytest.raises(RefusedError) as caught:
        content_types.resolve(choice, SCRIPT, detector)
    return caught.value.reason, caught.value.path, caught.value.detail


def test_a_named_content_type_that_does_not_exist_is_refused_naming_the_known_ones(
    tmp_path: Path,
) -> None:
    refusal = refusal_of(shipped(tmp_path), "ghost_story", AnsweringDetector("scary story"))

    assert refusal == (
        RefusalReason.CONTENT_TYPE_UNKNOWN,
        tmp_path / CONTENT_TYPES_FOLDER,
        "book_chapter, drug_story, scary_story",
    )


def test_auto_is_refused_when_the_answer_names_no_content_type(tmp_path: Path) -> None:
    refusal = refusal_of(shipped(tmp_path), "auto", AnsweringDetector("I cannot tell."))

    assert refusal == (
        RefusalReason.AUTO_UNRESOLVED,
        tmp_path / CONTENT_TYPES_FOLDER,
        "book_chapter, drug_story, scary_story",
    )
