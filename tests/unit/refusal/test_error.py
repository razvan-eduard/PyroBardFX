from pathlib import Path

import pytest

from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError

FOLDER = Path("content_types")
NAMES = "book_chapter, scary_story"


def test_a_placeholder_both_mappings_claim_is_refused_when_the_refusal_is_built() -> None:
    with pytest.raises(ValueError, match="choice"):
        RefusedError(
            RefusalReason.CONTENT_TYPE_UNKNOWN,
            FOLDER,
            NAMES,
            labelled={"choice": "adapters.family.llm"},
            literal={"choice": "ghost_story"},
        )


@pytest.mark.parametrize("fixed", ["path", "detail", "option", "env"])
def test_a_placeholder_the_printer_fills_for_every_refusal_is_refused_when_claimed(
    fixed: str,
) -> None:
    with pytest.raises(ValueError, match=fixed):
        RefusedError(
            RefusalReason.CONTENT_TYPE_UNKNOWN,
            FOLDER,
            NAMES,
            literal={"choice": "ghost_story", fixed: "x"},
        )


def test_a_refusal_built_without_a_value_for_a_placeholder_of_its_text_is_refused() -> None:
    with pytest.raises(ValueError, match="choice"):
        RefusedError(RefusalReason.CONTENT_TYPE_UNKNOWN, FOLDER, NAMES)


def test_the_labelled_and_literal_placeholders_cannot_be_passed_by_position() -> None:
    labelled = {"family": "adapters.family.llm"}

    with pytest.raises(TypeError):
        RefusedError(RefusalReason.CPU_REFUSED, None, "llm", labelled)  # ty: ignore[too-many-positional-arguments]


def test_the_message_of_a_refusal_names_each_literal_value() -> None:
    error = RefusedError(
        RefusalReason.CONTENT_TYPE_UNKNOWN, FOLDER, NAMES, literal={"choice": "ghost_story"}
    )

    assert "ghost_story" in str(error)
