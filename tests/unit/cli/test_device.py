import json
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from pyrobardfx.adapters.base import AdapterDeclaration
from pyrobardfx.adapters.constants import AdapterFamily, Backend, DeviceChoice, DType
from pyrobardfx.adapters.devices import BackendOrder
from pyrobardfx.cli.printer import CliPrinter
from pyrobardfx.locales.constants import Language
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.settings.model import Settings
from tests.builders.cli_app import CliAppBuilder
from tests.builders.working_directory import WorkingDirectoryBuilder
from tests.fakes.adapter import FakeAdapter
from tests.fakes.clock import FakeClock
from tests.fakes.devices import FakeBackendProbe

STORY = "the-lighthouse"
RUN_ID = "20261109T153000Z-a1b2"
APPLE_SILICON = FakeBackendProbe(Backend.MLX, Backend.MPS)


def run_on(
    sandbox: Path,
    device: str | None = None,
    setting: DeviceChoice = DeviceChoice.AUTO,
    probe: FakeBackendProbe | None = None,
) -> Result:
    working = WorkingDirectoryBuilder(sandbox / "work").story(STORY)
    root = working.settings(Settings(device=setting)).build()
    app = CliAppBuilder(sandbox).probe(probe or FakeBackendProbe()).build()
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

    assert backends_of(tmp_path) == ["mps", "mlx", "cpu"]


def test_with_no_device_flag_the_device_setting_decides(tmp_path: Path) -> None:
    run_on(tmp_path, setting=DeviceChoice.CPU, probe=APPLE_SILICON)

    assert backends_of(tmp_path) == ["cpu"]


def test_the_device_flag_wins_over_the_device_setting(tmp_path: Path) -> None:
    run_on(tmp_path, "mlx", setting=DeviceChoice.MPS, probe=APPLE_SILICON)

    assert backends_of(tmp_path) == ["mlx", "mps", "cpu"]


def test_an_auto_device_flag_wins_over_the_device_setting(tmp_path: Path) -> None:
    run_on(tmp_path, "auto", setting=DeviceChoice.CPU, probe=APPLE_SILICON)

    assert backends_of(tmp_path) == ["mlx", "mps", "cpu"]


def test_a_device_flag_naming_a_backend_the_machine_lacks_is_refused_with_no_run_folder(
    tmp_path: Path,
) -> None:
    result = run_on(tmp_path, "cuda", probe=APPLE_SILICON)

    runs = tmp_path / "work" / "stories" / STORY / "runs"
    assert (result.exit_code, list(runs.glob("*")) if runs.exists() else []) == (1, [])


def test_a_device_flag_naming_a_backend_the_machine_lacks_says_how_to_choose_another(
    tmp_path: Path,
) -> None:
    result = run_on(tmp_path, "cuda", probe=APPLE_SILICON)

    assert result.stderr.endswith(
        "Refused device cuda: this machine does not offer it. Pass --device auto to use what it "
        "offers, or name another device with --device or the device setting.\n"
    )


def print_refusal(order: BackendOrder, family: AdapterFamily, backend: Backend) -> None:
    """Print in en the refusal of an adapter of `family` that declares only `backend`."""
    declaration = AdapterDeclaration(family, {backend: DType.FLOAT16})
    with pytest.raises(RefusedError) as refused:
        FakeAdapter(order, FakeClock(), declaration)
    CliPrinter(Labels.load(Language.EN)).refused(refused.value)


def test_a_cpu_refusal_names_the_family_in_the_user_s_words(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_refusal(BackendOrder((Backend.CPU,)), AdapterFamily.DIFFUSION, Backend.CPU)

    assert capsys.readouterr().err.startswith(
        "Refused on the CPU (clip generation): it needs MPS, MLX or CUDA"
    )


def test_a_backend_refusal_names_the_family_in_the_user_s_words_and_the_backends(
    capsys: pytest.CaptureFixture[str],
) -> None:
    order = BackendOrder((Backend.MLX, Backend.MPS, Backend.CPU))

    print_refusal(order, AdapterFamily.STT, Backend.CUDA)

    assert capsys.readouterr().err.startswith(
        "Refused a model (transcription): its runtime runs on none of these backends, listed "
        "best first: mlx > mps > cpu."
    )
