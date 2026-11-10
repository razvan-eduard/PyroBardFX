import signal
from collections.abc import Iterator

import pytest

from tests.fakes.sigint import RecordingSigintHandler


@pytest.fixture
def previous_sigint() -> Iterator[RecordingSigintHandler]:
    """Install a recording SIGINT handler for the test; give back the process handler after."""
    handler = RecordingSigintHandler()
    before = signal.signal(signal.SIGINT, handler)
    yield handler
    signal.signal(signal.SIGINT, before)


@pytest.fixture
def default_previous_sigint() -> Iterator[None]:
    """Install Python's default SIGINT handler for the test; give back the process handler after."""
    before = signal.signal(signal.SIGINT, signal.default_int_handler)
    yield
    signal.signal(signal.SIGINT, before)


@pytest.fixture
def ignored_previous_sigint() -> Iterator[None]:
    """Ignore SIGINT for the test; give back the process handler after."""
    before = signal.signal(signal.SIGINT, signal.SIG_IGN)
    yield
    signal.signal(signal.SIGINT, before)
