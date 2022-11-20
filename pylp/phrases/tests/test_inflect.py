#!/usr/bin/env python
# coding: utf-8


from pylp.phrases.inflect import inflect_ru_phrase, inflect_phrase
from pylp.phrases.builder import Phrase
from pylp.common import (
    PosTag,
    WordGender,
    WordTense,
    WordVoice,
    WordNumber,
    WordCase,
    Lang,
    SyntLink,
)

from pylp.word_obj import WordObj
from pylp import lp_doc


def test_simple_adj_inflect():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['красивый', 'картина'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['красивая', 'картина']


def test_simple_participle_inflect():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['разорвать', 'полотно'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST, voice=WordVoice.PASS),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.NEUT),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['разорванное', 'полотно']

    p.set_words(['разорванный', 'полотно'])

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['разорванное', 'полотно']


def test_simple_participle_inflect2():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['думать', 'голова'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PRES, voice=WordVoice.ACT),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['думающая', 'голова']


def test_participle_inflect3():
    p = Phrase()
    p.set_head_pos(2)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['усилить', 'половой', 'производительность'])
    p.set_deps([2, 1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST, voice=WordVoice.PASS),
            WordObj(pos_tag=PosTag.ADJ),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['усиленная', 'половая', 'производительность']


def test_simple_noun_inflect():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1])
    p.set_words(['шляпа', 'капитан'])
    p.set_deps([0, -1])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.MASC, synt_link=SyntLink.NMOD),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['шляпа', 'капитана']


def test_plural_inflect():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['острый', 'ножницы'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR, gender=WordGender.FEM),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['острые', 'ножницы']


def test_plural_inflect2():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['красивый', 'пейзаж'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR, gender=WordGender.MASC),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['красивые', 'пейзажи']


def test_plural_inflect3():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['вооружённый', 'сила'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))
    sent = lp_doc.Sent(
        [
            WordObj(
                pos_tag=PosTag.PARTICIPLE,
                number=WordNumber.PLUR,
                case=WordCase.GEN,
                voice=WordVoice.PASS,
                tense=WordTense.PAST,
            ),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR, case=WordCase.GEN),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['вооружённые', 'силы']


def test_UN_inflect():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['организация', 'объединить', 'нация'])
    p.set_deps([0, 1, -2])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(
                pos_tag=PosTag.PARTICIPLE,
                number=WordNumber.PLUR,
                tense=WordTense.PAST,
                voice=WordVoice.PASS,
            ),
            WordObj(
                pos_tag=PosTag.NOUN,
                number=WordNumber.PLUR,
                gender=WordGender.FEM,
                synt_link=SyntLink.NMOD,
            ),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['организация', 'объединённых', 'наций']


def test_3phrase_inflect():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['результат', 'химический', 'реакция'])
    p.set_deps([0, 1, -2])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, case=WordCase.LOC),
            WordObj(pos_tag=PosTag.ADJ, gender=WordGender.FEM, case=WordCase.GEN),
            WordObj(
                pos_tag=PosTag.NOUN,
                gender=WordGender.FEM,
                case=WordCase.GEN,
                synt_link=SyntLink.NMOD,
            ),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words(False) == ['результат', 'химической', 'реакции']


def test_inflect_phrase():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['красивый', 'картина'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, lang=Lang.RU),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM, lang=Lang.RU),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['красивая', 'картина']


def test_inflect_ru_phrase_with_eng():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['народнолатинский', 'pernula'])
    p.set_deps([1, None])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, lang=Lang.RU),
            WordObj(pos_tag=PosTag.NOUN, lang=Lang.EN),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['народнолатинский', 'pernula']


def test_inflect_ru_phrase3():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1])
    p.set_words(['раковина', 'стромбус'])
    p.set_deps([0, -1])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.MASC, synt_link=SyntLink.NMOD),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['раковины', 'стромбуса']


def test_inflect_ru_phrase4():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['живой', 'глаз'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.MASC, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['живые', 'глаза']


def test_ru_propn_inflect1():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1])
    p.set_words(['бригадир', 'владычин'])
    p.set_deps([None, -1])
    p.set_extra([None] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.APPOS),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['бригадир', 'Владычин']


def test_ru_propn_inflect2():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1])
    p.set_words(['шляпа', 'валентина'])
    p.set_deps([None, -1])
    p.set_extra([None] * len(p.get_sent_pos_list()))
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.NMOD),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['шляпа', 'Валентины']


def test_ru_propn_inflect3():
    p = Phrase()
    p.set_head_pos(0)
    p.set_sent_pos_list([0, 1])
    p.set_words(['иван', 'иванов'])
    p.set_deps([0, -1])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PROPN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.FLAT),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['Иван', 'Иванов']


def test_ru_propn_inflect4():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['красивый', 'валентина', 'иванов'])
    p.set_deps([1, 0, -1])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ),
            WordObj(pos_tag=PosTag.PROPN, gender=WordGender.FEM),
            WordObj(pos_tag=PosTag.PROPN, gender=WordGender.FEM, synt_link=SyntLink.FLAT),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words(False) == ['красивая', 'Валентина', 'Иванова']


def test_simple_en_pres_part_inflect_1():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['fly', 'enemy'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE_ADVERB),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['flying', 'enemy']


def test_simple_en_pres_part_inflect_2():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['slide', 'window'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['sliding', 'window']


def test_simple_en_pres_part_inflect_3():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['can', 'food'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PRES),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['canning', 'food']


def test_simple_en_past_part_inflect_1():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['desire', 'objective'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['desired', 'objective']


def test_simple_en_past_part_inflect_2():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['employ', 'man'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['employed', 'man']


def test_simple_en_past_part_inflect_3():
    p = Phrase()
    p.set_head_pos(1)
    p.set_sent_pos_list([0, 1])
    p.set_words(['study', 'course'])
    p.set_deps([1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['studied', 'course']


def test_en_3phrase_inflect():
    p = Phrase()
    p.set_head_pos(2)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['undefine', 'fly', 'object'])
    p.set_deps([2, 1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.PARTICIPLE),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['undefined', 'flying', 'object']


def test_en_plural_inflect_1():
    p = Phrase()
    p.set_head_pos(2)
    p.set_sent_pos_list([0, 1, 2])
    p.set_words(['study', 'course', 'match'])
    p.set_deps([1, 1, 0])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['studies', 'courses', 'matches']


def test_en_plural_inflect_2():
    p = Phrase()
    p.set_head_pos(2)
    p.set_sent_pos_list([0, 1, 2, 3])
    p.set_words(['boy', 'kiss', 'wife', 'vertex'])
    p.set_deps([1, 1, 0, -1])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['boys', 'kisses', 'wives', 'vertices']


def test_en_plural_inflect_3():
    p = Phrase()
    p.set_head_pos(2)
    p.set_sent_pos_list([0, 1, 2, 3])
    p.set_words(['potato', 'child', 'mouse', 'crisis'])
    p.set_deps([1, 1, 0, -1])
    p.set_extra([{}] * len(p.get_sent_pos_list()))

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words(False) == ['Potatoes', 'Children', 'Mice', 'Crises']
