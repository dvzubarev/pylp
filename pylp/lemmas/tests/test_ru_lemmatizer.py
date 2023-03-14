#!/usr/bin/env python3


import pytest

from pylp.lemmas.lemmatizer import Lemmatizer
from pylp.lemmas.ru_lemmatizer import RuLemmatizer, RuLemmatizerOpts
from pylp import lp_doc
from pylp.common import Lang, PosTag, SyntLink, WordCase, WordGender, WordNumber, WordDegree
from pylp.word_obj import WordObj


@pytest.fixture
def ru_lemmatizer():
    return RuLemmatizer()


@pytest.fixture
def ru_lem_with_fix_feats():
    return RuLemmatizer(RuLemmatizerOpts(fix_feats=True))


@pytest.fixture
def general_lemmatizer():
    return Lemmatizer()


@pytest.fixture(
    scope='module',
    params=['ru', 'general'],
    ids=['RuLemmatizer', 'GeneralLemmatizier'],
)
def mp_lemmatizer(request):
    if request.param == 'ru':
        return RuLemmatizer()
    return Lemmatizer()


def _make_doc_obj(sents) -> lp_doc.Doc:
    doc = lp_doc.Doc('id', lang=Lang.RU)
    for s in sents:
        sent = lp_doc.Sent()
        for w in s:
            sent.add_word(w)
        doc.add_sent(sent)
    return doc


def test_ru_lem1(mp_lemmatizer):
    word1 = WordObj(form='прекрасна', pos_tag=PosTag.ADJ_SHORT)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'прекрасный'


def test_ru_lem2(mp_lemmatizer):
    word1 = WordObj(form='Потрачено', pos_tag=PosTag.PARTICIPLE_SHORT)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'потраченный'


def test_ru_lem3(mp_lemmatizer):
    word1 = WordObj(form='впустую', pos_tag=PosTag.ADV)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'впустую'


def test_ru_lem4(mp_lemmatizer):
    word1 = WordObj(
        form='выходные',
        pos_tag=PosTag.NOUN,
        # Wrong feats
        gender=WordGender.FEM,
        number=WordNumber.SING,
    )

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'выходной'


def test_ru_lem5(mp_lemmatizer):
    # войска is wrongly lemmatized to войска in SynTagRus
    # But its correctly lemmatized to войско in Taiga
    word1 = WordObj(
        form='войска',
        pos_tag=PosTag.NOUN,
        case=WordCase.ACC,
        number=WordNumber.PLUR,
        gender=WordGender.NEUT,
    )

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'войско'

    word1 = WordObj(
        form='погранвойсках',
        pos_tag=PosTag.NOUN,
        case=WordCase.LOC,
        number=WordNumber.PLUR,
        gender=WordGender.NEUT,
    )

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'погранвойско'


def test_ru_lem6(mp_lemmatizer):
    word1 = WordObj(form='Саудовской', pos_tag=PosTag.ADJ, synt_link=SyntLink.AMOD)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'саудовский'


def test_ru_lem7(mp_lemmatizer):
    word1 = WordObj(form='Иванова', pos_tag=PosTag.PROPN, case=WordCase.GEN, gender=WordGender.MASC)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma.lower() == 'иванов'

    # feats error; wrong gender
    word1 = WordObj(form='Иванова', pos_tag=PosTag.PROPN, case=WordCase.GEN, gender=WordGender.FEM)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma.lower() == 'иванов'

    # Does not work with pymorphy
    # old dictionaries?
    # https://github.com/pymorphy2/pymorphy2/issues/160
    # word1 = WordObj(form='Иванова', pos_tag=PosTag.PROPN, case=WordCase.NOM, gender=WordGender.FEM)
    # lemma = mp_lemmatizer.produce_lemma(word1)
    # assert lemma.lower() == 'ивановa'


def test_ru_lem_comp_num_1(mp_lemmatizer):
    word1 = WordObj(form='пятьсот', pos_tag=PosTag.NUM)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'пятьсот'

    word1 = WordObj(form='трехсот', pos_tag=PosTag.NUM)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'триста'


def test_ru_lem_comp_adj_1(mp_lemmatizer):
    word1 = WordObj(form='Быстрее', pos_tag=PosTag.ADJ)
    word1.degree = WordDegree.CMP
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'быстрый'

    word2 = WordObj(form='высочайшая', pos_tag=PosTag.ADJ)
    word2.degree = WordDegree.SUP
    lemma = mp_lemmatizer.produce_lemma(word2)
    assert lemma == 'высокий'


def test_ru_lem_comp_adj_2(mp_lemmatizer):
    word1 = WordObj(form='девяностых', pos_tag=PosTag.ADJ)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'девяностый'


def test_ru_lem_infn_1(mp_lemmatizer):
    word1 = WordObj(form='принимать', pos_tag=PosTag.VERB)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'принимать'


def test_punct_general(general_lemmatizer):
    word1 = WordObj(form=',', pos_tag=PosTag.PUNCT)
    lemma = general_lemmatizer.produce_lemma(word1)
    assert lemma == ','

    word1 = WordObj(form=',****##***,', pos_tag=PosTag.PUNCT)
    lemma = general_lemmatizer.produce_lemma(word1)
    assert lemma == ',****##***,'


def test_ru_feats_fix_1(ru_lem_with_fix_feats):
    word1 = WordObj(form='силы', pos_tag=PosTag.NOUN, number=WordNumber.PLUR)

    doc = _make_doc_obj([[word1]])

    ru_lem_with_fix_feats(doc)
    word_fixed = doc[0][0]
    assert word_fixed.lemma == 'сила'
    # shouldn't fix word number to SING
    assert word_fixed.number == WordNumber.PLUR


def test_ru_feats_fix_2(ru_lem_with_fix_feats):
    word1 = WordObj(
        form='выходные',
        pos_tag=PosTag.NOUN,
        gender=WordGender.FEM,
        number=WordNumber.SING,
    )

    doc = _make_doc_obj([[word1]])

    ru_lem_with_fix_feats(doc)
    word_fixed = doc[0][0]
    assert word_fixed.lemma == 'выходной'
    assert word_fixed.gender == WordGender.MASC
    assert word_fixed.number == WordNumber.PLUR
