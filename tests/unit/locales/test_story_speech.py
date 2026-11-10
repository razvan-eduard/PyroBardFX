from pyrobardfx.locales.constants import STORY_SPEECH, Language


def test_every_language_has_a_story_speech_entry() -> None:
    assert set(STORY_SPEECH) == set(Language)


def test_a_romanian_story_is_transcribed_as_ro_and_voiced_in_ro_ro() -> None:
    speech = STORY_SPEECH[Language.RO]

    assert (speech.whisper_language, speech.voice_locale) == ("ro", "ro-RO")


def test_an_english_story_is_voiced_in_en_us() -> None:
    assert STORY_SPEECH[Language.EN].voice_locale == "en-US"


def test_each_language_is_transcribed_under_its_two_letter_code() -> None:
    codes = {language: speech.whisper_language for language, speech in STORY_SPEECH.items()}

    assert codes == {
        Language.RO: "ro",
        Language.EN: "en",
        Language.FR: "fr",
        Language.DE: "de",
        Language.ES: "es",
    }


def test_each_other_language_is_voiced_in_its_home_country_locale() -> None:
    locales = {language: speech.voice_locale for language, speech in STORY_SPEECH.items()}

    assert {key: locales[key] for key in (Language.FR, Language.DE, Language.ES)} == {
        Language.FR: "fr-FR",
        Language.DE: "de-DE",
        Language.ES: "es-ES",
    }
