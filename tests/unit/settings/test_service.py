import json
from pathlib import Path

import pytest

from pyrobardfx.locales.constants import Language
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.settings.constants import QualityPresetName
from pyrobardfx.settings.model import Settings
from pyrobardfx.settings.service import SetAsideFile, SettingChange, SettingsService
from pyrobardfx.workdir.working_directory import WorkingDirectory
from tests.builders.fan_out import FanOutBuilder
from tests.fakes.clock import FakeClock
from tests.fakes.events import RecordingSink

NIGHT = Settings(runs_to_keep=9, quality_preset=QualityPresetName.BEST)
BEST_ONLY = Settings(quality_preset=QualityPresetName.BEST)
GLOBAL_ONLY = Settings(runs_to_keep=9, ui_language=Language.RO, story_language=Language.FR)
GLOBAL_AND_BEST = GLOBAL_ONLY.model_copy(update={"quality_preset": QualityPresetName.BEST})


def open_settings(root: Path, sink: RecordingSink | None = None) -> SettingsService:
    (root / "config").mkdir(parents=True, exist_ok=True)
    events = FanOutBuilder.over(FakeClock(), (sink or RecordingSink(),))
    return SettingsService.open(WorkingDirectory(root=root), FakeClock(), events)


def test_written_settings_read_back_after_the_working_directory_is_opened_again(
    tmp_path: Path,
) -> None:
    open_settings(tmp_path).write(NIGHT)

    assert open_settings(tmp_path).read() == NIGHT


def broken_settings(root: Path) -> Path:
    path = root / "config" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"runs_to_keep": "many"}', encoding="utf-8")
    return path


def test_a_broken_settings_file_is_set_aside_next_to_it_under_a_dated_name(
    tmp_path: Path,
) -> None:
    broken_settings(tmp_path)

    open_settings(tmp_path)

    assert sorted(path.name for path in (tmp_path / "config").iterdir()) == [
        "settings.broken-20261109T153000Z.json"
    ]


def test_a_file_set_aside_twice_in_one_second_keeps_both_backups(tmp_path: Path) -> None:
    path = broken_settings(tmp_path)
    open_settings(tmp_path)
    path.write_text('{"runs_to_keep": 0}', encoding="utf-8")

    open_settings(tmp_path)

    backups = (tmp_path / "config").iterdir()
    assert sorted(backup.read_text(encoding="utf-8") for backup in backups) == [
        '{"runs_to_keep": "many"}',
        '{"runs_to_keep": 0}',
    ]


def test_a_broken_settings_file_opens_with_the_default_settings(tmp_path: Path) -> None:
    broken_settings(tmp_path)

    assert open_settings(tmp_path).read() == Settings()


def test_a_broken_settings_file_is_kept_as_one_record_of_its_path_and_backup(
    tmp_path: Path,
) -> None:
    path = broken_settings(tmp_path)

    settings = open_settings(tmp_path)

    assert settings.take_set_aside() == (
        SetAsideFile(path=path, backup=path.with_name("settings.broken-20261109T153000Z.json")),
    )


def test_the_set_aside_records_are_handed_out_once(tmp_path: Path) -> None:
    broken_settings(tmp_path)
    settings = open_settings(tmp_path)
    settings.take_set_aside()

    assert settings.take_set_aside() == ()


def test_a_broken_settings_file_logs_one_set_aside_event_naming_the_backup(
    tmp_path: Path,
) -> None:
    path = broken_settings(tmp_path)
    sink = RecordingSink()

    open_settings(tmp_path, sink)

    assert [(event.event, event.stage, event.fields) for event in sink.events] == [
        (
            "settings_file_set_aside",
            "settings",
            {
                "path": str(path),
                "backup": str(path.with_name("settings.broken-20261109T153000Z.json")),
            },
        )
    ]


def presets_file(root: Path) -> dict[str, object]:
    return json.loads((root / "config" / "presets.json").read_text(encoding="utf-8"))


def test_a_saved_preset_holds_only_the_settings_that_differ_from_the_defaults(
    tmp_path: Path,
) -> None:
    settings = open_settings(tmp_path)
    settings.write(BEST_ONLY)

    settings.save_preset("night")

    assert presets_file(tmp_path)["presets"] == {"night": {"quality_preset": "best"}}


def test_saving_a_preset_under_a_taken_name_is_refused_naming_the_preset(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")

    with pytest.raises(RefusedError) as refused:
        settings.save_preset("night")

    assert (refused.value.reason, refused.value.detail) == (
        RefusalReason.PRESET_NAME_TAKEN,
        "night",
    )


def test_saving_with_overwrite_replaces_the_preset_of_a_taken_name(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.write(NIGHT)
    settings.save_preset("night")
    settings.write(BEST_ONLY)

    settings.save_preset("night", overwrite=True)

    assert presets_file(tmp_path)["presets"] == {"night": {"quality_preset": "best"}}


def test_overwriting_the_default_preset_keeps_it_the_default(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")
    settings.set_default_preset("night")
    settings.write(BEST_ONLY)

    settings.save_preset("night", overwrite=True)

    assert settings.presets().default == "night"


def test_a_saved_preset_holds_none_of_the_global_settings_even_when_they_differ(
    tmp_path: Path,
) -> None:
    settings = open_settings(tmp_path)
    settings.write(GLOBAL_AND_BEST)

    settings.save_preset("night")

    assert presets_file(tmp_path)["presets"] == {"night": {"quality_preset": "best"}}


def test_loading_a_preset_sets_its_fields_over_the_defaults_and_keeps_the_global_settings(
    tmp_path: Path,
) -> None:
    settings = open_settings(tmp_path)
    settings.write(BEST_ONLY)
    settings.save_preset("night")
    settings.write(GLOBAL_ONLY)

    settings.load_preset("night")

    assert open_settings(tmp_path).read() == GLOBAL_AND_BEST


def test_loading_a_preset_resets_the_other_settings_it_does_not_hold_to_the_defaults(
    tmp_path: Path,
) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("plain")
    settings.write(GLOBAL_AND_BEST)

    settings.load_preset("plain")

    assert open_settings(tmp_path).read() == GLOBAL_ONLY


def test_loading_a_preset_lists_each_setting_it_changed_with_its_old_and_new_value(
    tmp_path: Path,
) -> None:
    settings = open_settings(tmp_path)
    settings.write(BEST_ONLY)
    settings.save_preset("night")
    settings.write(GLOBAL_ONLY)

    changes = settings.load_preset("night")

    assert changes == (SettingChange(name="quality_preset", before="balanced", after="best"),)


def test_the_diff_of_a_preset_lists_what_a_load_would_change(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.write(BEST_ONLY)
    settings.save_preset("night")
    settings.write(GLOBAL_ONLY)

    diff = settings.preset_diff("night")

    assert (diff, diff == settings.load_preset("night")) == (
        (SettingChange(name="quality_preset", before="balanced", after="best"),),
        True,
    )


def test_a_preset_saved_holding_global_settings_loads_its_other_fields_and_keeps_those_in_place(
    tmp_path: Path,
) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "presets.json").write_text(
        '{"presets": {"night": {"quality_preset": "best", "runs_to_keep": 3,'
        ' "ui_language": "en", "story_language": "de"}}}',
        encoding="utf-8",
    )
    settings = open_settings(tmp_path)
    settings.write(GLOBAL_ONLY)

    settings.load_preset("night")

    assert (settings.presets().names, open_settings(tmp_path).read()) == (
        ("night",),
        GLOBAL_AND_BEST,
    )


def test_the_diff_of_a_preset_leaves_the_settings_as_they_are(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.write(BEST_ONLY)
    settings.save_preset("night")
    settings.write(Settings(runs_to_keep=9))

    settings.preset_diff("night")

    assert open_settings(tmp_path).read() == Settings(runs_to_keep=9)


@pytest.mark.parametrize("call", ["preset_diff", "rename_preset", "delete_preset"])
def test_an_unknown_preset_is_refused_naming_the_preset(tmp_path: Path, call: str) -> None:
    settings = open_settings(tmp_path)
    action = {
        "preset_diff": lambda: settings.preset_diff("dawn"),
        "rename_preset": lambda: settings.rename_preset("dawn", "dusk"),
        "delete_preset": lambda: settings.delete_preset("dawn"),
    }[call]

    with pytest.raises(RefusedError) as refused:
        action()

    assert (refused.value.reason, refused.value.detail) == (RefusalReason.PRESET_UNKNOWN, "dawn")


def test_loading_an_unknown_preset_is_refused_naming_the_preset(tmp_path: Path) -> None:
    with pytest.raises(RefusedError) as refused:
        open_settings(tmp_path).load_preset("dawn")

    assert (refused.value.reason, refused.value.detail) == (RefusalReason.PRESET_UNKNOWN, "dawn")


def test_a_renamed_preset_is_listed_under_its_new_name_only(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")

    settings.rename_preset("night", "dusk")

    assert open_settings(tmp_path).presets().names == ("dusk",)


def test_renaming_a_preset_onto_a_taken_name_is_refused_naming_that_name(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")
    settings.write(BEST_ONLY)
    settings.save_preset("dusk")

    with pytest.raises(RefusedError) as refused:
        settings.rename_preset("night", "dusk")

    assert (refused.value.reason, refused.value.detail) == (
        RefusalReason.PRESET_NAME_TAKEN,
        "dusk",
    )


def test_a_preset_set_as_default_is_listed_as_the_default(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")

    settings.set_default_preset("night")

    assert open_settings(tmp_path).presets().default == "night"


def test_setting_an_unknown_preset_as_default_is_refused_naming_the_preset(
    tmp_path: Path,
) -> None:
    with pytest.raises(RefusedError) as refused:
        open_settings(tmp_path).set_default_preset("dawn")

    assert (refused.value.reason, refused.value.detail) == (RefusalReason.PRESET_UNKNOWN, "dawn")


def test_a_deleted_preset_is_no_longer_listed(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")

    settings.delete_preset("night")

    assert open_settings(tmp_path).presets().names == ()


def test_deleting_the_default_preset_leaves_no_default(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")
    settings.set_default_preset("night")

    settings.delete_preset("night")

    assert open_settings(tmp_path).presets().default is None


def test_renaming_the_default_preset_keeps_it_the_default(tmp_path: Path) -> None:
    settings = open_settings(tmp_path)
    settings.save_preset("night")
    settings.set_default_preset("night")

    settings.rename_preset("night", "dusk")

    assert open_settings(tmp_path).presets().default == "dusk"


def test_a_working_directory_without_a_settings_file_starts_from_the_default_preset(
    tmp_path: Path,
) -> None:
    settings = open_settings(tmp_path)
    settings.write(BEST_ONLY)
    settings.save_preset("night")
    settings.set_default_preset("night")
    (tmp_path / "config" / "settings.json").unlink()

    assert open_settings(tmp_path).read() == BEST_ONLY


@pytest.mark.parametrize(
    "text",
    [
        '{"presets": {"night": {"runs_to_keep": 0}}}',
        '{"presets": {"night": {"brightness": 3}}}',
    ],
)
def test_a_presets_file_holding_a_preset_the_settings_refuse_is_set_aside(
    tmp_path: Path, text: str
) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "presets.json").write_text(text, encoding="utf-8")

    assert open_settings(tmp_path).presets().names == ()


def test_a_presets_file_whose_default_names_no_preset_is_set_aside(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "presets.json").write_text(
        '{"default": "dawn", "presets": {}}', encoding="utf-8"
    )

    assert open_settings(tmp_path).presets().default is None
