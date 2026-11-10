from pyrobardfx.script.model import Tag
from pyrobardfx.script.parser import ScriptParser


def tags_of(text: str) -> list[Tag]:
    script = ScriptParser().parse(text)
    return [
        tag
        for chapter in script.chapters
        for section in chapter.sections
        for paragraph in section.paragraphs
        for tag in paragraph.tags
    ]


def test_a_sound_tag_records_its_kind_value_and_the_spoken_words_before_it() -> None:
    (tag,) = tags_of("She opened the door [sfx: door] and left.")

    assert (tag.kind, tag.value, tag.word) == ("one-shot", "door", 4)


def test_a_sound_tag_reads_a_trailing_volume_and_fade_word_in_either_order() -> None:
    first, second = tags_of("[sfx: door, 0.8, fade long] [ambience: rain, fade short, 0.3]")

    assert [(t.value, t.volume, t.fade) for t in (first, second)] == [
        ("door", 0.8, "long"),
        ("rain", 0.3, "short"),
    ]


def test_a_tag_volume_is_held_between_zero_and_the_cap_of_two() -> None:
    loud, negative = tags_of("[sfx: boom, 3.5] [sfx: hush, -1]")

    assert (loud.volume, negative.volume) == (2.0, 0.0)


def test_visual_subject_fx_and_text_tags_keep_their_whole_text_as_the_value() -> None:
    tags = tags_of(
        "[scene: lsd | a harbour, 0.5] [subject: datura, 1] [fx: darken, 3, 0.8] [text: Act 2, 1]"
    )

    assert [(t.kind, t.value, t.volume) for t in tags] == [
        ("visual", "lsd | a harbour, 0.5", None),
        ("subject", "datura, 1", None),
        ("fx", "darken, 3, 0.8", None),
        ("text", "Act 2, 1", None),
    ]


def test_a_last_part_that_is_neither_volume_nor_fade_stays_in_the_value() -> None:
    (tag,) = tags_of("[sfx: door, creaky, 0.4]")

    assert (tag.value, tag.volume) == ("door, creaky", 0.4)


def test_a_sound_tag_reads_a_content_id_after_its_path() -> None:
    (tag,) = tags_of("[sfx: door/creak.wav #3FA2C1, 0.8]")

    assert (tag.value, tag.content_id, tag.volume) == ("door/creak.wav", "3fa2c1", 0.8)


def test_a_hash_shorter_than_six_hex_digits_is_no_content_id() -> None:
    (tag,) = tags_of("[sfx: door #3fa2]")

    assert (tag.value, tag.content_id) == ("door #3fa2", None)


def test_scene_is_read_as_visual_in_any_case() -> None:
    tags = tags_of("[SCENE: lsd | fog] [Sfx: door]")

    assert [t.kind for t in tags] == ["visual", "one-shot"]


def test_ambiance_is_no_tag_word_and_stays_spoken_text() -> None:
    (chapter,) = ScriptParser().parse("Rain [Ambiance: forest] fell.").chapters

    assert chapter.sections[0].paragraphs[0].text == "Rain [Ambiance: forest] fell."


def test_the_one_shot_kind_name_is_no_tag_word_and_stays_spoken_text() -> None:
    (chapter,) = ScriptParser().parse("The door [one-shot: door] shut.").chapters

    assert chapter.sections[0].paragraphs[0].text == "The door [one-shot: door] shut."


def test_a_music_tag_reads_volume_and_fade_as_a_sound_tag_does() -> None:
    (tag,) = tags_of("[music: main theme, 0.6, fade long]")

    assert (tag.kind, tag.value, tag.volume, tag.fade) == ("music", "main theme", 0.6, "long")


def test_a_bracket_of_an_unknown_kind_stays_spoken_text() -> None:
    (chapter,) = ScriptParser().parse("He said [hello: there] twice.").chapters

    assert chapter.sections[0].paragraphs[0].text == "He said [hello: there] twice."


def test_an_empty_tag_stays_a_tag_with_an_empty_value_and_is_never_spoken() -> None:
    (chapter,) = ScriptParser().parse("Door [sfx] shut [sfx: door].").chapters

    (paragraph,) = chapter.sections[0].paragraphs
    assert (paragraph.text, [(t.value, t.word) for t in paragraph.tags]) == (
        "Door shut .",
        [("", 1), ("door", 2)],
    )
