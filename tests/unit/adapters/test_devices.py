import pytest

from pyrobardfx.adapters.constants import Backend, DeviceChoice
from pyrobardfx.adapters.devices import DeviceResolver
from pyrobardfx.refusal.constants import RefusalReason
from pyrobardfx.refusal.error import RefusedError
from tests.fakes.devices import FakeDeviceProbe


def test_an_apple_silicon_machine_gets_mlx_then_mps_then_the_cpu() -> None:
    resolver = DeviceResolver(FakeDeviceProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.AUTO)

    assert order.backends == (Backend.MLX, Backend.MPS, Backend.CPU)


def test_an_nvidia_machine_gets_cuda_then_the_cpu() -> None:
    resolver = DeviceResolver(FakeDeviceProbe(Backend.CUDA))

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.AUTO)

    assert order.backends == (Backend.CUDA, Backend.CPU)


def test_a_machine_without_an_accelerator_gets_only_the_cpu() -> None:
    resolver = DeviceResolver(FakeDeviceProbe())

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.AUTO)

    assert order.backends == (Backend.CPU,)


def test_the_device_flag_puts_its_backend_alone_before_the_cpu() -> None:
    resolver = DeviceResolver(FakeDeviceProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.MPS, DeviceChoice.AUTO)

    assert order.backends == (Backend.MPS, Backend.CPU)


def test_the_device_flag_cpu_leaves_only_the_cpu() -> None:
    resolver = DeviceResolver(FakeDeviceProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.CPU, DeviceChoice.AUTO)

    assert order.backends == (Backend.CPU,)


def test_the_device_setting_overrides_the_automatic_choice() -> None:
    resolver = DeviceResolver(FakeDeviceProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.AUTO, DeviceChoice.CPU)

    assert order.backends == (Backend.CPU,)


def test_the_device_flag_wins_over_the_device_setting() -> None:
    resolver = DeviceResolver(FakeDeviceProbe(Backend.MPS, Backend.MLX))

    order = resolver.pick(DeviceChoice.MLX, DeviceChoice.CPU)

    assert order.backends == (Backend.MLX, Backend.CPU)


def test_a_device_choice_naming_a_backend_the_machine_lacks_is_refused_naming_it() -> None:
    resolver = DeviceResolver(FakeDeviceProbe(Backend.MPS, Backend.MLX))

    with pytest.raises(RefusedError) as refused:
        resolver.pick(DeviceChoice.CUDA, DeviceChoice.AUTO)

    assert (refused.value.reason, refused.value.detail) == (
        RefusalReason.DEVICE_UNAVAILABLE,
        "cuda",
    )
