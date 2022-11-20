#!/usr/bin/env python3


import pytest

from pylp.lemmas.ru_lemmatizer import RuLemmatizer
from pylp import lp_doc
from pylp.common import Lang, PosTag, WordGender, WordNumber
from pylp.word_obj import WordObj


@pytest.fixture
def ru_lemmatizer():
    return RuLemmatizer()


def _make_doc_obj(sents) -> lp_doc.Doc:
    doc = lp_doc.Doc('id', lang=Lang.RU)
    for s in sents:
        sent = lp_doc.Sent()
        for w in s:
            sent.add_word(w)
        doc.add_sent(sent)
    return doc


def test_ru_lem1(ru_lemmatizer):
    word1 = WordObj(lemma='прекрасть', form='прекрасна', pos_tag=PosTag.ADJ_SHORT)

    doc = _make_doc_obj([[word1]])

    ru_lemmatizer(doc)
    word_fixed = doc[0][0]
    assert word_fixed.lemma == 'прекрасный'


def test_ru_lem2(ru_lemmatizer):
    word1 = WordObj(lemma='тратить', form='Потрачено', pos_tag=PosTag.PARTICIPLE_SHORT)

    doc = _make_doc_obj([[word1]])

    ru_lemmatizer(doc)
    word_fixed = doc[0][0]
    assert word_fixed.lemma == 'потраченный'


def test_ru_lem3(ru_lemmatizer):
    word1 = WordObj(lemma='впустой', form='впустую', pos_tag=PosTag.ADV)

    doc = _make_doc_obj([[word1]])

    ru_lemmatizer(doc)
    word_fixed = doc[0][0]
    assert word_fixed.lemma == 'впустую'


def test_ru_lem4(ru_lemmatizer):
    word1 = WordObj(
        lemma='выходная',
        form='выходные',
        pos_tag=PosTag.NOUN,
        gender=WordGender.FEM,
        number=WordNumber.SING,
    )

    doc = _make_doc_obj([[word1]])

    ru_lemmatizer(doc)
    word_fixed = doc[0][0]
    assert word_fixed.lemma == 'выходной'
    assert word_fixed.gender == WordGender.MASC
    assert word_fixed.number == WordNumber.PLUR


def test_ru_lem5(ru_lemmatizer):
    word1 = WordObj(lemma='сила', form='силы', pos_tag=PosTag.NOUN, number=WordNumber.PLUR)

    doc = _make_doc_obj([[word1]])

    ru_lemmatizer(doc)
    word_fixed = doc[0][0]
    # shouldn't fix word number to SING
    assert word_fixed.number == WordNumber.PLUR
