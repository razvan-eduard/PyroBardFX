from pathlib import Path

import pytest

from pyrobardfx.cli.constants import WORKING_DIR_OPTION
from pyrobardfx.cli.printer import CliPrinter
from pyrobardfx.locales.constants import LOCALES_FOLDER, Language
from pyrobardfx.locales.labels import Labels
from pyrobardfx.refusal.constants import FIXED_PLACEHOLDERS, RefusalReason
from pyrobardfx.refusal.error import RefusedError
from pyrobardfx.workdir.constants import HOME_OVERRIDE_ENV

REASON = RefusalReason.NO_STORY
STORY = Path("story.txt")
DETAIL = "gone"
SEPARATOR = "|"


def test_the_printer_fills_each_placeholder_every_refusal_text_may_hold(
    capsys: pytest.CaptureFixture[str],
) -> None:
    texts: dict[str, str] = {
        REASON: SEPARATOR.join(f"{{{name}}}" for name in sorted(FIXED_PLACEHOLDERS))
    }
    labels = Labels(Language.EN, LOCALES_FOLDER, texts, texts)

    CliPrinter(labels).refused(RefusedError(REASON, STORY, DETAIL))

    assert set(capsys.readouterr().err.rstrip("\n").split(SEPARATOR)) == {
        str(STORY),
        DETAIL,
        WORKING_DIR_OPTION,
        HOME_OVERRIDE_ENV,
    }
