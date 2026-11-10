import signal

import pytest

from pyrobardfx.cli.interrupt import SigintCancel
from tests.fakes.cancel import FakeCancelToken
from tests.fakes.sigint import RecordingSigintHandler


def test_sigint_during_the_span_cancels_the_token(previous_sigint: RecordingSigintHandler) -> None:
    token = FakeCancelToken()

    with SigintCancel(token):
        signal.raise_signal(signal.SIGINT)

    assert (token.is_cancelled(), previous_sigint.calls) == (True, 0)


def test_the_span_gives_back_the_previous_handler(previous_sigint: RecordingSigintHandler) -> None:
    with SigintCancel(FakeCancelToken()):
        pass

    assert signal.getsignal(signal.SIGINT) is previous_sigint


def test_a_span_that_raises_gives_back_the_previous_handler(
    previous_sigint: RecordingSigintHandler,
) -> None:
    with pytest.raises(RuntimeError), SigintCancel(FakeCancelToken()):
        raise RuntimeError

    assert signal.getsignal(signal.SIGINT) is previous_sigint


def test_sigint_after_the_span_reaches_the_previous_handler_and_cancels_nothing(
    previous_sigint: RecordingSigintHandler,
) -> None:
    token = FakeCancelToken()
    with SigintCancel(token):
        pass

    signal.raise_signal(signal.SIGINT)

    assert (token.is_cancelled(), previous_sigint.calls) == (False, 1)
