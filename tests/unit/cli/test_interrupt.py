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


def test_a_second_sigint_during_the_span_reaches_the_previous_handler_once(
    previous_sigint: RecordingSigintHandler,
) -> None:
    token = FakeCancelToken()

    with SigintCancel(token):
        signal.raise_signal(signal.SIGINT)
        signal.raise_signal(signal.SIGINT)

    assert (token.is_cancelled(), previous_sigint.calls) == (True, 1)


def test_each_sigint_after_the_second_during_the_span_reaches_the_previous_handler(
    previous_sigint: RecordingSigintHandler,
) -> None:
    with SigintCancel(FakeCancelToken()):
        for _ in range(4):
            signal.raise_signal(signal.SIGINT)

    assert previous_sigint.calls == 3


def test_a_span_entered_again_starts_counting_again(
    previous_sigint: RecordingSigintHandler,
) -> None:
    interrupt = SigintCancel(FakeCancelToken())
    with interrupt:
        signal.raise_signal(signal.SIGINT)
        signal.raise_signal(signal.SIGINT)

    with interrupt:
        signal.raise_signal(signal.SIGINT)

    assert previous_sigint.calls == 1


def test_the_first_sigint_of_a_new_span_cancels_its_own_token_only(
    previous_sigint: RecordingSigintHandler,
) -> None:
    with SigintCancel(FakeCancelToken()):
        signal.raise_signal(signal.SIGINT)
        signal.raise_signal(signal.SIGINT)
    token = FakeCancelToken()

    with SigintCancel(token):
        signal.raise_signal(signal.SIGINT)

    assert (token.is_cancelled(), previous_sigint.calls) == (True, 1)


@pytest.mark.usefixtures("default_previous_sigint")
def test_a_second_sigint_during_the_span_raises_keyboard_interrupt_under_the_default_handler() -> (
    None
):
    with pytest.raises(KeyboardInterrupt), SigintCancel(FakeCancelToken()):
        signal.raise_signal(signal.SIGINT)
        signal.raise_signal(signal.SIGINT)


@pytest.mark.usefixtures("ignored_previous_sigint")
def test_a_second_sigint_during_the_span_gives_an_ignored_sigint_back_to_be_ignored() -> None:
    with SigintCancel(FakeCancelToken()):
        signal.raise_signal(signal.SIGINT)
        signal.raise_signal(signal.SIGINT)
        handler = signal.getsignal(signal.SIGINT)

    assert handler is signal.SIG_IGN
