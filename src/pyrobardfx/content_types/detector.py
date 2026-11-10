"""The seam `auto` detection goes through: a model reads the script and names a Content type."""

from abc import ABC, abstractmethod


class ContentTypeDetector(ABC):
    """Reads a script and answers, in its own words, which of the offered Content types it is."""

    @abstractmethod
    def answer(self, script: str, names: tuple[str, ...]) -> str:
        """The model's answer for `script`, given the name of each Content type it may pick."""
