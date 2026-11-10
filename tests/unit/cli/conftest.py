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
