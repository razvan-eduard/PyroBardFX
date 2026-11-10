from pathlib import Path

from pyrobardfx.content_types.catalogue import ContentTypes
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


def test_auto_takes_the_drug_story_when_the_answer_names_no_content_type(tmp_path: Path) -> None:
    detector = AnsweringDetector("I cannot tell.")

    assert shipped(tmp_path).resolve("auto", SCRIPT, detector) == "drug_story"
