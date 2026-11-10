from pathlib import Path

from pyrobardfx.locales import constants
from pyrobardfx.locales.constants import LOCALES_FOLDER


def test_the_locales_folder_is_the_folder_of_the_locales_package() -> None:
    assert Path(constants.__file__).parent == LOCALES_FOLDER
