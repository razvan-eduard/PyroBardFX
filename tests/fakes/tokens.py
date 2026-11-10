"""The fake token source: known tokens in a known order, so run ids are known in advance."""


class FixedTokenSource:
    """Returns its tokens in order, then the last one again; refuses a length nobody asked for."""

    def __init__(self, *tokens: str) -> None:
        self._tokens = list(tokens)

    def hex(self, nbytes: int) -> str:
        token = self._tokens.pop(0) if len(self._tokens) > 1 else self._tokens[0]
        if len(token) != 2 * nbytes:
            raise ValueError(f"fake token {token!r} is not {nbytes} bytes of hex")
        return token
