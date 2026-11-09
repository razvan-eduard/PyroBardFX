from pathlib import Path

import pytest
import structlog
from typer.testing import CliRunner

from pyrobardfx.cli.app import CliApp
from tests.builders.host_facts import HostFactsBuilder

LAYOUT = {
    "config",
    "stories",
    "library",
    "models",
    "cache",
    "looks",
    "content_types",
    "locales-override",
}


def test_first_start_on_macos_creates_the_working_directory_in_documents(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).platform("darwin").build()

    CliRunner().invoke(CliApp.build(host), [])

    root = host.home / "Documents" / "PyroBardFX"
    assert {child.name for child in root.iterdir()} == LAYOUT


def test_first_start_on_linux_creates_the_working_directory_in_the_home_folder(
    tmp_path: Path,
) -> None:
    host = HostFactsBuilder(tmp_path).platform("linux").build()

    CliRunner().invoke(CliApp.build(host), [])

    assert {child.name for child in (host.home / "PyroBardFX").iterdir()} == LAYOUT


def test_first_start_on_windows_creates_the_working_directory_in_documents(
    tmp_path: Path,
) -> None:
    host = HostFactsBuilder(tmp_path).platform("win32").build()

    CliRunner().invoke(CliApp.build(host), [])

    root = host.home / "Documents" / "PyroBardFX"
    assert {child.name for child in root.iterdir()} == LAYOUT


def test_the_working_dir_option_puts_the_working_directory_where_it_points(
    tmp_path: Path,
) -> None:
    host = HostFactsBuilder(tmp_path).build()
    chosen = tmp_path / "external-disk" / "stories"

    CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert {child.name for child in chosen.iterdir()} == LAYOUT


def test_pyrobardfx_home_puts_the_working_directory_where_it_points(tmp_path: Path) -> None:
    chosen = tmp_path / "external-disk" / "stories"
    host = HostFactsBuilder(tmp_path).env("PYROBARDFX_HOME", str(chosen)).build()

    CliRunner().invoke(CliApp.build(host), [])

    assert {child.name for child in chosen.iterdir()} == LAYOUT


def test_the_working_dir_option_wins_over_pyrobardfx_home(tmp_path: Path) -> None:
    from_env = tmp_path / "from-env"
    from_option = tmp_path / "from-option"
    host = HostFactsBuilder(tmp_path).env("PYROBARDFX_HOME", str(from_env)).build()

    CliRunner().invoke(CliApp.build(host), ["--working-dir", str(from_option)])

    assert (from_option.is_dir(), from_env.exists()) == (True, False)


def test_a_working_directory_in_the_temp_folder_is_refused_with_its_reason(
    tmp_path: Path,
) -> None:
    host = HostFactsBuilder(tmp_path).build()
    chosen = host.system_temp / "stories"

    result = CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert "is inside the temporary folder" in result.output


def test_a_refused_working_directory_is_never_created(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).build()
    chosen = host.system_temp / "stories"

    CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert not chosen.exists()


def test_a_refused_start_exits_with_a_failure_code(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).build()

    result = CliRunner().invoke(
        CliApp.build(host), ["--working-dir", str(host.system_temp / "stories")]
    )

    assert result.exit_code == 1


def test_a_working_directory_under_tmpdir_is_refused(tmp_path: Path) -> None:
    tmpdir = tmp_path / "user-temp"
    host = HostFactsBuilder(tmp_path).env("TMPDIR", str(tmpdir)).build()

    result = CliRunner().invoke(CliApp.build(host), ["--working-dir", str(tmpdir / "stories")])

    assert "is inside the temporary folder" in result.output


def test_a_working_directory_under_a_fixed_temp_root_is_refused(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).build()
    chosen = host.fixed_temp_roots[0] / "stories"

    result = CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert "is inside the temporary folder" in result.output


def test_a_working_directory_reached_through_a_link_into_temp_is_refused(
    tmp_path: Path,
) -> None:
    host = HostFactsBuilder(tmp_path).build()
    host.system_temp.mkdir()
    link = tmp_path / "looks-safe"
    link.symlink_to(host.system_temp, target_is_directory=True)

    result = CliRunner().invoke(CliApp.build(host), ["--working-dir", str(link / "stories")])

    assert "is inside the temporary folder" in result.output


def test_a_working_directory_in_temp_spelled_in_another_case_is_refused(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).build()
    host.system_temp.mkdir()
    other_case = tmp_path / host.system_temp.name.upper()
    if not other_case.exists():
        pytest.skip("the file system tells letter case apart")

    result = CliRunner().invoke(CliApp.build(host), ["--working-dir", str(other_case / "stories")])

    assert "is inside the temporary folder" in result.output


def test_a_filesystem_root_as_tmpdir_is_never_a_temp_root(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).env("TMPDIR", tmp_path.anchor).build()
    chosen = tmp_path / "stories"

    CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert chosen.is_dir()


def test_a_relative_tmpdir_is_never_a_temp_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    host = HostFactsBuilder(tmp_path).env("TMPDIR", "work").build()
    chosen = tmp_path / "work" / "stories"

    CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert chosen.is_dir()


def test_a_working_directory_that_cannot_be_created_is_refused_with_its_reason(
    tmp_path: Path,
) -> None:
    host = HostFactsBuilder(tmp_path).build()
    occupied = tmp_path / "a-file"
    occupied.write_text("not a folder")

    result = CliRunner().invoke(CliApp.build(host), ["--working-dir", str(occupied)])

    assert "cannot be created" in result.output


def test_first_start_logs_that_it_created_the_working_directory(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).build()
    chosen = tmp_path / "stories"

    with structlog.testing.capture_logs() as events:
        CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert [(e["event"], e["path"]) for e in events] == [("working_directory_created", str(chosen))]


def test_a_later_start_logs_that_it_opened_the_working_directory(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).build()
    chosen = tmp_path / "stories"
    CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    with structlog.testing.capture_logs() as events:
        CliRunner().invoke(CliApp.build(host), ["--working-dir", str(chosen)])

    assert [(e["event"], e["path"]) for e in events] == [("working_directory_opened", str(chosen))]


def test_a_working_directory_event_carries_its_stage_and_percent(tmp_path: Path) -> None:
    host = HostFactsBuilder(tmp_path).build()

    with structlog.testing.capture_logs() as events:
        CliRunner().invoke(CliApp.build(host), ["--working-dir", str(tmp_path / "stories")])

    assert [(e["stage"], e["percent"]) for e in events] == [("working_directory_open", 100.0)]
