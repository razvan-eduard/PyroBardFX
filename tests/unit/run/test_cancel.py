from pyrobardfx.run.cancel import ThreadCancelToken


def test_a_new_cancel_token_says_the_run_was_not_asked_to_stop() -> None:
    assert ThreadCancelToken().is_cancelled() is False


def test_a_cancel_token_says_the_run_was_asked_to_stop_once_cancelled() -> None:
    token = ThreadCancelToken()

    token.cancel()

    assert token.is_cancelled() is True
