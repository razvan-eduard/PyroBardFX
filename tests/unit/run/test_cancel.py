from pyrobardfx.run.cancel import CancelFlag


def test_a_new_cancel_flag_says_the_run_was_not_asked_to_stop() -> None:
    assert CancelFlag().is_cancelled() is False


def test_a_cancel_flag_says_the_run_was_asked_to_stop_once_cancelled() -> None:
    flag = CancelFlag()

    flag.cancel()

    assert flag.is_cancelled() is True
