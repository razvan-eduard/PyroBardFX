"""The fake cancel token: says cancelled from a chosen check on, as the job manager would."""


class FakeCancelToken:
    """Counts the checks it answers; from check number `cancel_at` on, it says cancelled."""

    def __init__(self, cancel_at: int | None = None) -> None:
        self._cancel_at = cancel_at
        self.checks = 0

    def is_cancelled(self) -> bool:
        self.checks += 1
        return self._cancel_at is not None and self.checks >= self._cancel_at
