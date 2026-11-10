"""The fake Content type detector: gives one set answer and keeps what it was asked."""

from pyrobardfx.content_types.detector import ContentTypeDetector


class AnsweringDetector(ContentTypeDetector):
    """Answers `reply` to every question; keeps each script and the names it was offered."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.asked: list[tuple[str, tuple[str, ...]]] = []

    def answer(self, script: str, names: tuple[str, ...]) -> str:
        self.asked.append((script, names))
        return self.reply
