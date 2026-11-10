from types import ModuleType

import pytest

from pyrobardfx.adapters.constants import Backend, DeviceChoice
from pyrobardfx.adapters.devices import DeviceResolver, SystemBackendProbe
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from tests.fakes.devices import FakeBackendProbe


def test_an_apple_silicon_machine_gets_mlx_then_mps_then_the_cpu() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.AUTO)

    assert order.backends == (Backend.MLX, Backend.MPS, Backend.CPU)


def test_an_nvidia_machine_gets_cuda_then_the_cpu() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.CUDA))

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.AUTO)

    assert order.backends == (Backend.CUDA, Backend.CPU)


def test_a_machine_without_an_accelerator_gets_only_the_cpu() -> None:
    resolver = DeviceResolver(FakeBackendProbe())

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.AUTO)

    assert order.backends == (Backend.CPU,)


def test_naming_mps_puts_it_before_its_apple_silicon_partner_mlx() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.MPS, DeviceChoice.AUTO)

    assert order.backends == (Backend.MPS, Backend.MLX, Backend.CPU)


def test_naming_mlx_puts_it_before_its_apple_silicon_partner_mps() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.MLX, DeviceChoice.AUTO)

    assert order.backends == (Backend.MLX, Backend.MPS, Backend.CPU)


def test_naming_an_apple_backend_whose_partner_the_machine_lacks_leaves_it_alone() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS))

    order = resolver.pick(DeviceChoice.MPS, DeviceChoice.AUTO)

    assert order.backends == (Backend.MPS, Backend.CPU)


def test_the_device_setting_naming_mps_keeps_its_partner_mlx_too() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(None, DeviceChoice.MPS)

    assert order.backends == (Backend.MPS, Backend.MLX, Backend.CPU)


def test_naming_cuda_puts_it_alone_before_the_cpu() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX, Backend.CUDA))

    order = resolver.pick(DeviceChoice.CUDA, DeviceChoice.AUTO)

    assert order.backends == (Backend.CUDA, Backend.CPU)


def test_the_device_flag_cpu_leaves_only_the_cpu() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.CPU, DeviceChoice.AUTO)

    assert order.backends == (Backend.CPU,)


def test_with_no_device_flag_the_device_setting_decides() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(None, DeviceChoice.CPU)

    assert order.backends == (Backend.CPU,)


def test_an_auto_device_flag_wins_over_the_device_setting_and_asks_the_probe() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.CPU)

    assert order.backends == (Backend.MLX, Backend.MPS, Backend.CPU)


def test_the_device_flag_wins_over_the_device_setting() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.CPU, DeviceChoice.MLX)

    assert order.backends == (Backend.CPU,)


def test_a_device_choice_naming_a_backend_the_machine_lacks_is_refused_naming_it() -> None:
    resolver = DeviceResolver(FakeBackendProbe(Backend.MPS, Backend.MLX))

    with pytest.raises(RefusedError) as refused:
        resolver.pick(DeviceChoice.CUDA, DeviceChoice.AUTO)

    assert (refused.value.reason, refused.value.detail) == (
        RefusalReason.DEVICE_UNAVAILABLE,
        "cuda",
    )


def failing_to_load(name: str) -> ModuleType:
    """An import of `name` whose runtime is installed but whose native library will not load."""
    raise OSError(name)


@pytest.mark.parametrize("backend", [Backend.MLX, Backend.MPS, Backend.CUDA])
def test_a_runtime_whose_library_fails_to_load_offers_no_backend(backend: Backend) -> None:
    assert SystemBackendProbe(failing_to_load).available(backend) is False
