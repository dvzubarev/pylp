#!/usr/bin/env python3

import pytest

from pylp.lemmas.lemmatizer import Lemmatizer
from pylp.lemmas.en_lemmatizer import EnLemmatizer
from pylp.common import (
    PosTag,
    WordNumber,
    WordDegree,
    WordPerson,
    WordTense,
)
from pylp.word_obj import WordObj


@pytest.fixture(scope='module')
def en_lemmatizer():
    return EnLemmatizer()


@pytest.fixture(scope='module')
def general_lemmatizer():
    return Lemmatizer()


@pytest.fixture(
    scope='module',
    params=['en', 'general'],
    ids=['EnLemmatizer', 'GeneralLemmatizier'],
)
def mp_lemmatizer(request):
    if request.param == 'en':
        return EnLemmatizer()
    return Lemmatizer()


def test_en_lem_1(mp_lemmatizer):
    word1 = WordObj(form='Fears', pos_tag=PosTag.PROPN, number=WordNumber.PLUR)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'fear'


def test_en_lem_2(mp_lemmatizer):
    word1 = WordObj(form='Relations', pos_tag=PosTag.NOUN, number=WordNumber.PLUR)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'relation'


def test_en_lem_3(mp_lemmatizer):
    # word is not in en dictionary, also it is missing in wordnet too
    word1 = WordObj(form='maricultures', pos_tag=PosTag.NOUN, number=WordNumber.PLUR)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'mariculture'


def test_en_lem_4(mp_lemmatizer):
    word1 = WordObj(form='Times', pos_tag=PosTag.NOUN, number=WordNumber.SING)

    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'times'


def test_en_lem_5(mp_lemmatizer):
    word1 = WordObj(form='axes', pos_tag=PosTag.NOUN, number=WordNumber.PLUR)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'ax'


def test_en_lem_6(mp_lemmatizer):
    word1 = WordObj(form='quicker', pos_tag=PosTag.ADJ, degree=WordDegree.CMP)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'quick'


def test_en_lem_7(mp_lemmatizer):
    word1 = WordObj(form='hardest', pos_tag=PosTag.ADJ, degree=WordDegree.SUP)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'hard'


def test_en_lem_8(mp_lemmatizer):
    word1 = WordObj(form='goes', pos_tag=PosTag.VERB, tense=WordTense.PRES, person=WordPerson.III)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'go'


def test_en_lem_9(mp_lemmatizer):
    word1 = WordObj(form='sanitized', pos_tag=PosTag.PARTICIPLE, tense=WordTense.PAST)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'sanitize'

    word1 = WordObj(form='postponed', pos_tag=PosTag.VERB, tense=WordTense.PAST)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'postpone'


def test_en_lem_10(mp_lemmatizer):
    word1 = WordObj(form='sanitizing', pos_tag=PosTag.PARTICIPLE, tense=WordTense.PRES)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'sanitize'

    word1 = WordObj(form='exploring', pos_tag=PosTag.GERUND)
    lemma = mp_lemmatizer.produce_lemma(word1)
    assert lemma == 'explore'
