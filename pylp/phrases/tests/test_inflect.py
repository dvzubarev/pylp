#!/usr/bin/env python
# coding: utf-8


from pylp.phrases.inflect import inflect_ru_phrase, inflect_phrase
from pylp.phrases.phrase import Phrase
from pylp.common import (
    PosTag,
    WordAnimacy,
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

# * Ru Inflect tests


def test_simple_adj_inflect():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['красивый', 'картина'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ),
            WordObj(
                pos_tag=PosTag.NOUN,
                gender=WordGender.FEM,
                case=WordCase.ACC,
                animacy=WordAnimacy.INAN,
            ),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['красивая', 'картина']


def test_simple_participle_inflect():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['разорвать', 'полотно'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST, voice=WordVoice.PASS),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.NEUT),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['разорванное', 'полотно']

    p._words = ['разорванный', 'полотно']

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['разорванное', 'полотно']


def test_simple_participle_inflect2():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['думать', 'голова'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PRES, voice=WordVoice.ACT),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['думающая', 'голова']


def test_participle_inflect3():
    p = Phrase(
        head_pos=2,
        sent_pos_list=[0, 1, 2],
        words=['усилить', 'половой', 'производительность'],
        deps=[2, 1, 0],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST, voice=WordVoice.PASS),
            WordObj(pos_tag=PosTag.ADJ),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['усиленная', 'половая', 'производительность']


def test_simple_noun_inflect():
    p = Phrase(head_pos=0, sent_pos_list=[0, 1], words=['шляпа', 'капитан'], deps=[0, -1])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
            WordObj(
                pos_tag=PosTag.NOUN,
                gender=WordGender.MASC,
                synt_link=SyntLink.NMOD,
                case=WordCase.GEN,
            ),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['шляпа', 'капитана']


def test_simple_noun_inflect_2():
    p = Phrase(head_pos=0, sent_pos_list=[0, 1], words=['точка', 'зрение'], deps=[0, -1])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
            WordObj(
                pos_tag=PosTag.NOUN,
                gender=WordGender.NEUT,
                synt_link=SyntLink.COMPOUND,
                case=WordCase.GEN,
            ),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['точка', 'зрения']


def test_plural_inflect():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['острый', 'ножницы'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR, gender=WordGender.FEM),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['острые', 'ножницы']


def test_plural_inflect2():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['красивый', 'пейзаж'], deps=[1, 0])
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR, gender=WordGender.MASC),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['красивые', 'пейзажи']


def test_plural_inflect3():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['вооружённый', 'сила'], deps=[1, 0])
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
    assert p.get_words() == ['вооружённые', 'силы']


def test_UN_inflect():
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2],
        words=['организация', 'объединённый', 'нация'],
        deps=[0, 1, -2],
    )

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
                case=WordCase.GEN,
            ),
        ]
    )

    inflect_ru_phrase(p, sent)
    assert p.get_words() == ['организация', 'объединённых', 'наций']


def test_3phrase_inflect():
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2],
        words=['результат', 'химический', 'реакция'],
        deps=[0, 1, -2],
    )

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
    assert p.get_words() == ['результат', 'химической', 'реакции']


def test_inflect_phrase_with_wrong_doc_lang():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['красивый', 'картина'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, lang=Lang.RU),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM, lang=Lang.RU),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['красивая', 'картина']


def test_inflect_phrase_unsupported_case():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['темп', 'томп'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, case=WordCase.PAR, synt_link=SyntLink.NMOD),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['темп', 'томп']


def test_inflect_ru_phrase_with_eng():
    p = Phrase(
        head_pos=1, sent_pos_list=[0, 1], words=['народнолатинский', 'pernula'], deps=[1, None]
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, lang=Lang.RU),
            WordObj(pos_tag=PosTag.NOUN, lang=Lang.EN),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['народнолатинский', 'pernula']


def test_inflect_ru_phrase3():
    p = Phrase(head_pos=0, sent_pos_list=[0, 1], words=['раковина', 'стромбус'], deps=[0, -1])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.FEM, number=WordNumber.PLUR),
            WordObj(
                pos_tag=PosTag.NOUN,
                gender=WordGender.MASC,
                synt_link=SyntLink.NMOD,
                case=WordCase.GEN,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['раковины', 'стромбуса']


def test_inflect_ru_with_prep_1():
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2],
        words=['путь', 'к', 'вершина'],
        deps=[0, 1, -2],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.MASC),
            WordObj(pos_tag=PosTag.ADP),
            WordObj(
                pos_tag=PosTag.NOUN,
                gender=WordGender.FEM,
                synt_link=SyntLink.NMOD,
                case=WordCase.DAT,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['путь', 'к', 'вершине']


def test_inflect_ru_with_prep_2():
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 2, 3],
        words=['путь', 'красивый', 'вершина'],
        deps=[0, 1, -2],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.MASC),
            WordObj(pos_tag=PosTag.ADP),
            WordObj(pos_tag=PosTag.ADJ, number=WordNumber.PLUR, case=WordCase.DAT),
            WordObj(
                pos_tag=PosTag.NOUN,
                number=WordNumber.PLUR,
                synt_link=SyntLink.NMOD,
                case=WordCase.DAT,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['путь', 'красивым', 'вершинам']


def test_inflect_ru_with_prep_3():
    # напиток из шиповника и яблок
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 4],
        words=['напиток', 'яблоко'],
        deps=[0, -1],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.MASC),
            WordObj(pos_tag=PosTag.ADP),
            WordObj(
                pos_tag=PosTag.NOUN, case=WordCase.GEN, parent_offs=-2, synt_link=SyntLink.NMOD
            ),
            WordObj(pos_tag=PosTag.CCONJ),
            WordObj(
                pos_tag=PosTag.NOUN,
                parent_offs=-2,
                number=WordNumber.PLUR,
                synt_link=SyntLink.CONJ,
                case=WordCase.GEN,
            ),
            WordObj(pos_tag=PosTag.PUNCT),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['напиток', 'яблок']


def test_inflect_ru_phrase4():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['живой', 'глаз'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, gender=WordGender.MASC, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['живые', 'глаза']


def test_inflect_ru_phrase5():
    p = Phrase(head_pos=0, sent_pos_list=[0, 1], words=['область', 'финансы'], deps=[0, -1])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(
                pos_tag=PosTag.NOUN,
                gender=WordGender.MASC,
                number=WordNumber.PLUR,
                case=WordCase.GEN,
                synt_link=SyntLink.NMOD,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['область', 'финансов']


def test_ru_propn_inflect1():
    p = Phrase(head_pos=0, sent_pos_list=[0, 1], words=['бригадир', 'владычин'], deps=[0, -1])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.APPOS),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['бригадир', 'Владычин']


def test_ru_propn_inflect2():
    p = Phrase(head_pos=0, sent_pos_list=[0, 1], words=['шляпа', 'валентина'], deps=[0, -1])
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.NMOD, case=WordCase.GEN),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['шляпа', 'Валентины']


def test_ru_propn_inflect3():
    p = Phrase(head_pos=0, sent_pos_list=[0, 1], words=['иван', 'иванов'], deps=[0, -1])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PROPN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.FLAT),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['Иван', 'Иванов']


def test_ru_propn_inflect4():
    p = Phrase(
        head_pos=1,
        sent_pos_list=[0, 1, 2],
        words=['красивый', 'валентина', 'иванов'],
        deps=[1, 0, -1],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.ADJ),
            WordObj(pos_tag=PosTag.PROPN, gender=WordGender.FEM, case=WordCase.NOM),
            WordObj(
                pos_tag=PosTag.PROPN,
                gender=WordGender.FEM,
                synt_link=SyntLink.FLAT,
                case=WordCase.NOM,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['красивая', 'Валентина', 'Иванова']


def test_ru_propn_inflect5():
    p = Phrase(
        head_pos=0, sent_pos_list=[0, 1, 2], words=['шляпа', 'иван', 'иванов'], deps=[0, -1, -1]
    )
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.NMOD, case=WordCase.GEN),
            WordObj(pos_tag=PosTag.PROPN, synt_link=SyntLink.FLAT, case=WordCase.GEN),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['шляпа', 'Ивана', 'Иванова']


# ** Ru verb phrases inflect tests


def test_ru_vp_inflect1():
    # проголосуйте на выборах президента
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2, 3],
        words=['проголосовать', 'на', 'выборы', 'президент'],
        deps=[0, 1, -2, -1],
    )
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.VERB),
            WordObj(pos_tag=PosTag.ADP),
            WordObj(
                pos_tag=PosTag.NOUN,
                synt_link=SyntLink.OBL,
                number=WordNumber.PLUR,
                case=WordCase.LOC,
            ),
            WordObj(
                pos_tag=PosTag.NOUN,
                synt_link=SyntLink.NMOD,
                case=WordCase.ACC,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['проголосовать', 'на', 'выборах', 'президента']


def test_ru_vp_inflect2():
    # Я протер вымытую посуду
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2],
        words=['протереть', 'вымытый', 'посуда'],
        deps=[0, 1, -2],
    )
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.VERB),
            WordObj(pos_tag=PosTag.PARTICIPLE, synt_link=SyntLink.AMOD),
            WordObj(
                pos_tag=PosTag.NOUN,
                synt_link=SyntLink.OBJ,
                case=WordCase.ACC,
                gender=WordGender.FEM,
                animacy=WordAnimacy.INAN,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['протереть', 'вымытую', 'посуду']


def test_ru_vp_inflect3():
    # провести быстрые эксперименты
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2],
        words=['провести', 'быстрый', 'эксперимент'],
        deps=[0, 1, -2],
    )
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.VERB),
            WordObj(pos_tag=PosTag.ADJ, synt_link=SyntLink.AMOD),
            WordObj(
                pos_tag=PosTag.NOUN,
                synt_link=SyntLink.OBJ,
                case=WordCase.ACC,
                number=WordNumber.PLUR,
                animacy=WordAnimacy.INAN,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['провести', 'быстрые', 'эксперименты']


def test_ru_vp_inflect4():
    # пасти быстрых коз
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2],
        words=['пасти', 'быстрый', 'коза'],
        deps=[0, 1, -2],
    )
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.VERB),
            WordObj(pos_tag=PosTag.ADJ, synt_link=SyntLink.AMOD),
            WordObj(
                pos_tag=PosTag.NOUN,
                synt_link=SyntLink.OBJ,
                gender=WordGender.FEM,
                case=WordCase.ACC,
                number=WordNumber.PLUR,
                animacy=WordAnimacy.ANIM,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['пасти', 'быстрых', 'коз']


def test_ru_vp_inflect5():
    # добывать дешёвое сырьё
    p = Phrase(
        head_pos=0,
        sent_pos_list=[0, 1, 2],
        words=['добывать', 'дешёвый', 'сырьё'],
        deps=[0, 1, -2],
    )
    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.VERB),
            WordObj(pos_tag=PosTag.ADJ, synt_link=SyntLink.AMOD),
            WordObj(
                pos_tag=PosTag.NOUN,
                synt_link=SyntLink.OBJ,
                gender=WordGender.NEUT,
                case=WordCase.ACC,
                animacy=WordAnimacy.INAN,
            ),
        ]
    )

    inflect_phrase(p, sent, Lang.RU)
    assert p.get_words() == ['добывать', 'дешёвое', 'сырьё']


# * En inflect tests


def test_simple_en_pres_part_inflect_1():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['fly', 'enemy'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.GERUND),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['flying', 'enemy']


def test_simple_en_pres_part_inflect_2():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['slide', 'window'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['sliding', 'window']


def test_simple_en_pres_part_inflect_3():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['can', 'food'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PRES),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['canning', 'food']


def test_simple_en_pres_part_inflect_4():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['fielding', 'side'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['fielding', 'side']


def test_simple_en_past_part_inflect_1():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['desire', 'objective'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['desired', 'objective']


def test_simple_en_past_part_inflect_2():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['employ', 'man'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['employed', 'man']


def test_simple_en_past_part_inflect_3():
    p = Phrase(head_pos=1, sent_pos_list=[0, 1], words=['study', 'course'], deps=[1, 0])

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['studied', 'course']


def test_en_3phrase_inflect():
    p = Phrase(
        head_pos=2, sent_pos_list=[0, 1, 2], words=['undefine', 'fly', 'object'], deps=[2, 1, 0]
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST),
            WordObj(pos_tag=PosTag.PARTICIPLE),
            WordObj(pos_tag=PosTag.NOUN),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['undefined', 'flying', 'object']


def test_en_plural_inflect_1():
    p = Phrase(
        head_pos=2, sent_pos_list=[0, 1, 2], words=['study', 'course', 'match'], deps=[1, 1, 0]
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['studies', 'courses', 'matches']


def test_en_plural_inflect_2():
    p = Phrase(
        head_pos=2,
        sent_pos_list=[0, 1, 2, 3],
        words=['boy', 'kiss', 'wife', 'vertex'],
        deps=[1, 1, 0, -1],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['boys', 'kisses', 'wives', 'vertices']


def test_en_plural_inflect_3():
    p = Phrase(
        head_pos=2,
        sent_pos_list=[0, 1, 2, 3],
        words=['potato', 'child', 'mouse', 'crisis'],
        deps=[1, 1, 0, -1],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.PROPN, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['Potatoes', 'Children', 'Mice', 'Crises']


def test_en_plural_inflect_4():
    p = Phrase(
        head_pos=1,
        sent_pos_list=[0, 1, 2, 3],
        words=['many', 'people', 'man', 'woman'],
        deps=[1, 0, -1, -2],
    )

    sent = lp_doc.Sent(
        [
            WordObj(pos_tag=PosTag.NOUN),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
            WordObj(pos_tag=PosTag.NOUN, number=WordNumber.PLUR),
        ]
    )

    inflect_phrase(p, sent, Lang.EN)
    assert p.get_words() == ['many', 'people', 'men', 'women']
