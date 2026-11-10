"""The fake cancel token: says cancelled from a chosen check on, as the job manager would."""


class FakeCancelToken:
    """Counts the checks it answers; says cancelled from check number `cancel_at` on, or once
    `cancel()` was called."""

    def __init__(self, cancel_at: int | None = None) -> None:
        self._cancel_at = cancel_at
        self._cancelled = False
        self.checks = 0

    def cancel(self) -> None:
        """Say cancelled at every check from now on, as `ThreadCancelToken.cancel` does."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        self.checks += 1
        reached = self._cancel_at is not None and self.checks >= self._cancel_at
        return self._cancelled or reached
