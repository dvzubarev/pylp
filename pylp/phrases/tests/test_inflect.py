#!/usr/bin/env python
# coding: utf-8


from pylp.phrases.inflect import inflect_ru_phrase, inflect_phrase
from pylp.phrases.builder import Phrase
from pylp.common import Attr, PosTag, WordGender, WordTense, WordVoice, WordNumber, WordCase, Lang


def test_simple_adj_inflect():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['красивый', 'картина'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.ADJ},
        {Attr.POS_TAG: PosTag.NOUN, Attr.GENDER: WordGender.FEM},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['красивая', 'картина']


def test_simple_participle_inflect():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['разорвать', 'полотно'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.PARTICIPLE, Attr.TENSE: WordTense.PAST, Attr.VOICE: WordVoice.PASS},
        {Attr.POS_TAG: PosTag.NOUN, Attr.GENDER: WordGender.NEUT},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['разорванное', 'полотно']


def test_simple_participle_inflect2():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['думать', 'голова'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.PARTICIPLE, Attr.TENSE: WordTense.PRES},
        {Attr.POS_TAG: PosTag.NOUN, Attr.GENDER: WordGender.FEM},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['думающая', 'голова']


def test_simple_noun_inflect():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1])
    p.set_words(['шляпа', 'капитан'])
    p.set_deps([None, -1])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.NOUN, Attr.GENDER: WordGender.FEM},
        {Attr.POS_TAG: PosTag.NOUN, Attr.GENDER: WordGender.MASC},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['шляпа', 'капитана']


def test_plural_inflect():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['острый', 'ножницы'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.ADJ, Attr.PLURAL: WordNumber.PLUR},
        {Attr.POS_TAG: PosTag.NOUN, Attr.PLURAL: WordNumber.PLUR, Attr.GENDER: WordGender.FEM},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['острые', 'ножницы']


def test_plural_inflect2():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['красивый', 'пейзаж'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.ADJ, Attr.PLURAL: WordNumber.PLUR},
        {Attr.POS_TAG: PosTag.NOUN, Attr.PLURAL: WordNumber.PLUR, Attr.GENDER: WordGender.MASC},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['красивые', 'пейзажи']


def test_UN_inflect():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['организация', 'объединить', 'нация'])
    p.set_deps([None, 1, -2])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.NOUN},
        {
            Attr.POS_TAG: PosTag.PARTICIPLE,
            Attr.PLURAL: WordNumber.PLUR,
            Attr.TENSE: WordTense.PAST,
            Attr.VOICE: WordVoice.PASS,
        },
        {Attr.POS_TAG: PosTag.NOUN, Attr.PLURAL: WordNumber.PLUR, Attr.GENDER: WordGender.FEM},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['организация', 'объединённых', 'наций']


def test_3phrase_inflect():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['результат', 'химический', 'реакция'])
    p.set_deps([None, 1, -2])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.NOUN, Attr.CASE: WordCase.LOC},
        {Attr.POS_TAG: PosTag.ADJ, Attr.GENDER: WordGender.FEM, Attr.CASE: WordCase.GEN},
        {Attr.POS_TAG: PosTag.NOUN, Attr.GENDER: WordGender.FEM, Attr.CASE: WordCase.GEN},
    ]

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['результат', 'химической', 'реакции']


def test_inflect_phrase():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['красивый', 'картина'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.ADJ, Attr.LANG: Lang.RU},
        {Attr.POS_TAG: PosTag.NOUN, Attr.GENDER: WordGender.FEM, Attr.LANG: Lang.RU},
    ]

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['красивая', 'картина']


def test_inflect_ru_phrase_with_eng():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['народнолатинский', 'pernula'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = [
        {Attr.POS_TAG: PosTag.ADJ, Attr.LANG: Lang.RU},
        {Attr.POS_TAG: PosTag.NOUN, Attr.LANG: Lang.EN},
    ]

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['народнолатинский', 'pernula']
