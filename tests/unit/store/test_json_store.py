import os
from pathlib import Path

import pytest
from pydantic import BaseModel

from pyrobardfx.store.json_store import JsonStore


class Shelf(BaseModel):
    name: str
    level: float


DEFAULT = Shelf(name="empty", level=0.0)


def test_a_written_store_reads_back_as_indented_json_text(tmp_path: Path) -> None:
    path = tmp_path / "shelf.json"
    store = JsonStore.open(path, DEFAULT)

    store.write(Shelf(name="Pădure", level=0.5))

    assert path.read_text(encoding="utf-8") == '{\n  "name": "Pădure",\n  "level": 0.5\n}\n'


def test_a_store_opened_on_an_existing_file_reads_its_values(tmp_path: Path) -> None:
    path = tmp_path / "shelf.json"
    path.write_text('{"name": "Ploaie", "level": 0.8}', encoding="utf-8")

    store = JsonStore.open(path, DEFAULT)

    assert store.read() == Shelf(name="Ploaie", level=0.8)


def test_a_store_opened_without_a_file_reads_the_default(tmp_path: Path) -> None:
    store = JsonStore.open(tmp_path / "shelf.json", DEFAULT)

    assert store.read() == DEFAULT


def test_a_store_opened_without_a_file_writes_no_file(tmp_path: Path) -> None:
    JsonStore.open(tmp_path / "shelf.json", DEFAULT)

    assert list(tmp_path.iterdir()) == []


def test_a_store_reads_the_value_it_last_wrote(tmp_path: Path) -> None:
    store = JsonStore.open(tmp_path / "shelf.json", DEFAULT)

    store.write(Shelf(name="Vânt", level=0.3))

    assert store.read() == Shelf(name="Vânt", level=0.3)


def test_reads_come_from_memory_not_from_a_file_changed_behind_the_store(
    tmp_path: Path,
) -> None:
    path = tmp_path / "shelf.json"
    store = JsonStore.open(path, DEFAULT)
    store.write(Shelf(name="Vânt", level=0.3))
    path.write_text('{"name": "edited", "level": 1.0}', encoding="utf-8")

    assert store.read() == Shelf(name="Vânt", level=0.3)


class WriteCutShortError(Exception):
    """Stands in for a crash between writing the bytes and making them durable."""


def cut_writes_short(monkeypatch: pytest.MonkeyPatch) -> None:
    def crash(_fd: int) -> None:
        raise WriteCutShortError

    monkeypatch.setattr(os, "fsync", crash)


def test_a_write_cut_short_leaves_the_old_file_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "shelf.json"
    store = JsonStore.open(path, DEFAULT)
    store.write(Shelf(name="Pădure", level=0.5))
    cut_writes_short(monkeypatch)

    with pytest.raises(WriteCutShortError):
        store.write(Shelf(name="Furtună", level=0.9))

    assert path.read_text(encoding="utf-8") == '{\n  "name": "Pădure",\n  "level": 0.5\n}\n'


def test_a_first_write_cut_short_leaves_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = JsonStore.open(tmp_path / "shelf.json", DEFAULT)
    cut_writes_short(monkeypatch)

    with pytest.raises(WriteCutShortError):
        store.write(Shelf(name="Furtună", level=0.9))

    assert list(tmp_path.iterdir()) == []


def test_a_write_cut_short_keeps_the_old_value_in_memory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = JsonStore.open(tmp_path / "shelf.json", DEFAULT)
    store.write(Shelf(name="Pădure", level=0.5))
    cut_writes_short(monkeypatch)

    with pytest.raises(WriteCutShortError):
        store.write(Shelf(name="Furtună", level=0.9))

    assert store.read() == Shelf(name="Pădure", level=0.5)


def test_changing_a_read_value_leaves_the_store_unchanged(tmp_path: Path) -> None:
    store = JsonStore.open(tmp_path / "shelf.json", DEFAULT)
    store.write(Shelf(name="Pădure", level=0.5))

    store.read().level = 2.0

    assert store.read() == Shelf(name="Pădure", level=0.5)


def test_changing_a_written_value_afterwards_leaves_the_store_unchanged(tmp_path: Path) -> None:
    store = JsonStore.open(tmp_path / "shelf.json", DEFAULT)
    written = Shelf(name="Pădure", level=0.5)
    store.write(written)

    written.level = 2.0

    assert store.read() == Shelf(name="Pădure", level=0.5)


def test_a_broken_file_is_moved_whole_to_the_backup_path(tmp_path: Path) -> None:
    path, backup = tmp_path / "shelf.json", tmp_path / "shelf.broken.json"
    path.write_text('{"name": "Ploaie", "lev', encoding="utf-8")

    JsonStore.open_or_set_aside(path, DEFAULT, backup)

    assert (path.exists(), backup.read_text(encoding="utf-8")) == (False, '{"name": "Ploaie", "lev')


def test_a_store_opened_on_a_file_that_breaks_its_model_reads_the_default(tmp_path: Path) -> None:
    path = tmp_path / "shelf.json"
    path.write_text('{"name": "Ploaie", "level": "high"}', encoding="utf-8")

    store, _ = JsonStore.open_or_set_aside(path, DEFAULT, tmp_path / "shelf.broken.json")

    assert store.read() == DEFAULT


def test_a_broken_file_set_aside_names_the_backup_it_went_to(tmp_path: Path) -> None:
    path, backup = tmp_path / "shelf.json", tmp_path / "shelf.broken.json"
    path.write_text('{"name": "Ploaie", "level": "high"}', encoding="utf-8")

    _, set_aside = JsonStore.open_or_set_aside(path, DEFAULT, backup)

    assert set_aside == backup


def test_a_broken_file_whose_backup_path_is_taken_goes_to_a_numbered_one(tmp_path: Path) -> None:
    path, backup = tmp_path / "shelf.json", tmp_path / "shelf.broken.json"
    backup.write_text("earlier", encoding="utf-8")
    path.write_text('{"name": "Ploaie", "level": "high"}', encoding="utf-8")

    _, set_aside = JsonStore.open_or_set_aside(path, DEFAULT, backup)

    assert (set_aside, backup.read_text(encoding="utf-8")) == (
        tmp_path / "shelf.broken-2.json",
        "earlier",
    )


def test_a_store_opened_on_a_sound_file_sets_nothing_aside(tmp_path: Path) -> None:
    path = tmp_path / "shelf.json"
    path.write_text('{"name": "Ploaie", "level": 0.8}', encoding="utf-8")

    store, set_aside = JsonStore.open_or_set_aside(path, DEFAULT, tmp_path / "shelf.broken.json")

    assert (store.read(), set_aside) == (Shelf(name="Ploaie", level=0.8), None)
