"""The trash of the running system, through send2trash."""

from pathlib import Path

from send2trash import send2trash

from pyrobardfx.trash.base import Trash


class Send2TrashTrash(Trash):
    """Moves paths to the system trash with send2trash, which raises `OSError` when it cannot."""

    def _move(self, path: Path) -> None:
        send2trash(path)
