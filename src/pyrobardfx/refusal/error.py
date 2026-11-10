"""The one error every refusal raises, so one printer method and one `except` serve them all."""

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

from pyrobardfx.refusal.constants import (
    CLAIMED_TWICE_MESSAGE,
    FURTHER_PLACEHOLDERS,
    REFUSED_LITERAL_MESSAGE,
    REFUSED_MESSAGE,
    REFUSED_WITHOUT_PATH_MESSAGE,
    WRONG_PLACEHOLDERS_MESSAGE,
    RefusalReason,
)


class RefusedError(Exception):
    """A start or a Run was refused; `reason` keys its text, `detail` says what stood in its way.

    `path` is the file or folder the refusal concerns; a refusal about no path, such as a device
    choice, has none. Each further placeholder of the text sits in exactly one of two mappings:
    `labelled` maps it to the label key of its value, which the refusal's renderer resolves in the
    user's language; `literal` maps it to its value as it is, such as a name the user typed. The
    two together name exactly the further placeholders of `reason`, else `ValueError`.
    """

    def __init__(
        self,
        reason: RefusalReason,
        path: Path | None,
        detail: str,
        *,
        labelled: Mapping[str, str] | None = None,
        literal: Mapping[str, str] | None = None,
    ) -> None:
        self.reason = reason
        self.path = path
        self.detail = detail
        self.labelled: Mapping[str, str] = MappingProxyType(dict(labelled or {}))
        self.literal: Mapping[str, str] = MappingProxyType(dict(literal or {}))
        self._check_placeholders()
        message_format = REFUSED_WITHOUT_PATH_MESSAGE if path is None else REFUSED_MESSAGE
        message = message_format.format(reason=reason, path=path, detail=detail)
        super().__init__(
            message
            + "".join(
                REFUSED_LITERAL_MESSAGE.format(name=name, value=value)
                for name, value in self.literal.items()
            )
        )

    def _check_placeholders(self) -> None:
        """Refuse a placeholder both mappings claim, and a set other than the reason needs."""
        claimed_twice = self.labelled.keys() & self.literal.keys()
        if claimed_twice:
            raise ValueError(CLAIMED_TWICE_MESSAGE.format(names=sorted(claimed_twice)))
        given = self.labelled.keys() | self.literal.keys()
        needed = FURTHER_PLACEHOLDERS.get(self.reason, frozenset())
        if given != needed:
            message = WRONG_PLACEHOLDERS_MESSAGE.format(
                reason=self.reason, needed=sorted(needed), given=sorted(given)
            )
            raise ValueError(message)
