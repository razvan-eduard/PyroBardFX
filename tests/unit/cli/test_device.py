import json
from pathlib import Path

from typer.testing import CliRunner, Result

from pyrobardfx.adapters.constants import Backend, DeviceChoice
from pyrobardfx.settings.model import Settings
from tests.builders.cli_app import CliAppBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder
from tests.fakes.devices import FakeDeviceProbe

STORY = "the-lighthouse"
RUN_ID = "20261109T153000Z-a1b2"
APPLE_SILICON = FakeDeviceProbe(Backend.MLX, Backend.MPS)


def run_on(
    sandbox: Path,
    device: str | None = None,
    setting: DeviceChoice = DeviceChoice.AUTO,
    probe: FakeDeviceProbe | None = None,
) -> Result:
    working = WorkingDirectoryBuilder(sandbox / "work").story(STORY)
    root = working.settings(Settings(device=setting)).build()
    app = CliAppBuilder(sandbox).devices(probe or FakeDeviceProbe()).build()
    flag = [] if device is None else ["--device", device]
    return CliRunner().invoke(app, ["--working-dir", str(root), *flag, "run", STORY])


def backends_of(sandbox: Path) -> list[str]:
    folder = sandbox / "work" / "stories" / STORY / "runs" / RUN_ID
    snapshot = json.loads((folder / "snapshot.json").read_text())
    return snapshot["backend_order"]["backends"]


def test_a_run_given_a_device_flag_naming_a_backend_finishes(tmp_path: Path) -> None:
    assert run_on(tmp_path, "cpu").exit_code == 0


def test_a_device_flag_naming_no_backend_is_refused_as_a_usage_error(tmp_path: Path) -> None:
    assert run_on(tmp_path, "tpu").exit_code == 2


def test_the_help_offers_the_device_flag_with_auto_and_each_backend(tmp_path: Path) -> None:
    result = CliRunner().invoke(CliAppBuilder(tmp_path).build(), ["--help"])

    assert all(name in result.stdout for name in ("--device", "auto", "mps", "mlx", "cuda", "cpu"))


def test_the_device_setting_alone_picks_the_backends_of_the_run(tmp_path: Path) -> None:
    run_on(tmp_path, setting=DeviceChoice.MPS, probe=APPLE_SILICON)

    assert backends_of(tmp_path) == ["mps", "cpu"]


def test_the_device_flag_wins_over_the_device_setting(tmp_path: Path) -> None:
    run_on(tmp_path, "mlx", setting=DeviceChoice.MPS, probe=APPLE_SILICON)

    assert backends_of(tmp_path) == ["mlx", "cpu"]


def test_an_auto_device_flag_leaves_the_device_setting_in_charge(tmp_path: Path) -> None:
    run_on(tmp_path, "auto", setting=DeviceChoice.CPU, probe=APPLE_SILICON)

    assert backends_of(tmp_path) == ["cpu"]


def test_a_device_flag_naming_a_backend_the_machine_lacks_is_refused_with_no_run_folder(
    tmp_path: Path,
) -> None:
    result = run_on(tmp_path, "cuda", probe=APPLE_SILICON)

    runs = tmp_path / "work" / "stories" / STORY / "runs"
    assert (result.exit_code, list(runs.glob("*")) if runs.exists() else []) == (1, [])
    assert "Refused device cuda: this machine does not offer it." in result.stderr
