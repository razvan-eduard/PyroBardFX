"""The source of the random part of a run id."""

import secrets
from typing import Protocol


class TokenSource(Protocol):
    """Gives random hex text."""

    def hex(self, nbytes: int) -> str:
        """Return `nbytes` random bytes as hex, two characters per byte."""
        ...


class SecretsTokenSource:
    """Draws tokens from the operating system's random source."""

    def hex(self, nbytes: int) -> str:
        return secrets.token_hex(nbytes)
