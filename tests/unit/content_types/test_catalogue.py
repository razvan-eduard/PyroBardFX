from pathlib import Path

from pyrobardfx.content_types.catalogue import ContentTypes
from pyrobardfx.content_types.model import ContentType
from pyrobardfx.locales.constants import Language
from pyrobardfx.locales.labels import Labels
from pyrobardfx.workdir.constants import CONTENT_TYPES_FOLDER
from pyrobardfx.workdir.working_directory import WorkingDirectory


def write_own(
    root: Path, name: str, look: str, keywords: dict[str, dict[str, tuple[str, ...]]]
) -> None:
    """Write the creator's own Content type `name` into the working directory at `root`."""
    own = ContentType(
        label_key=f"own.{name}",
        quality="",
        negative="",
        styles={"fog": "grey fog"},
        keywords=keywords,
        default_look=look,
        sound_mix={},
    )
    folder = root / CONTENT_TYPES_FOLDER
    folder.mkdir(exist_ok=True)
    (folder / f"{name}.json").write_text(own.model_dump_json(), encoding="utf-8")


def test_three_content_types_ship_with_the_app(tmp_path: Path) -> None:
    content_types = ContentTypes.load(WorkingDirectory(root=tmp_path))

    assert content_types.names() == ("book_chapter", "drug_story", "scary_story")


def test_a_shipped_content_type_brings_its_default_look_and_sound_mix(tmp_path: Path) -> None:
    scary = ContentTypes.load(WorkingDirectory(root=tmp_path)).get("scary_story")

    assert (scary.default_look, scary.sound_mix["effects"]) == ("horror", 0.8)


def test_the_shipped_content_types_hold_english_keyword_lists_only(tmp_path: Path) -> None:
    content_types = ContentTypes.load(WorkingDirectory(root=tmp_path))

    languages = {name: set(content_types.get(name).keywords) for name in content_types.names()}

    assert languages == {"book_chapter": {"en"}, "drug_story": {"en"}, "scary_story": {"en"}}


def test_the_drug_story_matches_each_of_its_styles_but_sober_narration_by_english_words(
    tmp_path: Path,
) -> None:
    drug = ContentTypes.load(WorkingDirectory(root=tmp_path)).get("drug_story")

    assert set(drug.styles) - set(drug.keywords["en"]) == {"sober narration"}


def test_a_content_type_in_the_working_directory_loads_beside_the_shipped_ones(
    tmp_path: Path,
) -> None:
    write_own(tmp_path, "ghost_story", "calm", {"en": {"fog": ("fog*",)}})

    names = ContentTypes.load(WorkingDirectory(root=tmp_path)).names()

    assert names == ("book_chapter", "drug_story", "ghost_story", "scary_story")


def test_a_content_type_of_the_creator_takes_the_place_of_a_shipped_one_of_its_name(
    tmp_path: Path,
) -> None:
    write_own(tmp_path, "scary_story", "calm", {"en": {}})

    scary = ContentTypes.load(WorkingDirectory(root=tmp_path)).get("scary_story")

    assert scary.default_look == "calm"


def test_a_keyword_list_of_another_language_is_one_more_key_in_the_data_file(
    tmp_path: Path,
) -> None:
    write_own(tmp_path, "ghost_story", "calm", {"en": {}, "de": {"fog": ("nebel*",)}})

    ghost = ContentTypes.load(WorkingDirectory(root=tmp_path)).get("ghost_story")

    assert ghost.keywords["de"] == {"fog": ("nebel*",)}


def test_each_shipped_content_type_is_named_from_the_locales(tmp_path: Path) -> None:
    content_types = ContentTypes.load(WorkingDirectory(root=tmp_path))
    labels = Labels.load(Language.EN)

    named = {labels.label(content_types.get(name).label_key) for name in content_types.names()}

    assert named == {"Book chapter", "Drug story", "Scary story"}
