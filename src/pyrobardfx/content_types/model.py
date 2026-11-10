"""The Content type data file: what one family of stories brings to a Run."""

from pydantic import BaseModel, ConfigDict

from pyrobardfx.store.constants import EXTRA_FORBID


class ContentType(BaseModel):
    """One Content type's data file.

    `styles` maps each style's name to its picture prompt wording. `keywords` maps a story language
    to each style's match words, a trailing `*` matching any ending; a new language is a new key.
    `sound_mix` maps a layer kind's name to the level it plays at in this Content type.
    """

    model_config = ConfigDict(frozen=True, extra=EXTRA_FORBID)

    label_key: str
    quality: str
    negative: str
    styles: dict[str, str]
    keywords: dict[str, dict[str, tuple[str, ...]]]
    default_look: str
    sound_mix: dict[str, float]
