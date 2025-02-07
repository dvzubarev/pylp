#!/usr/bin/env python3

import pytest

from pylp import lp_doc

from pylp.phrases.util import add_phrases_to_doc
import pylp.common as lp
from pylp.word_obj import WordObj


def _mkw(lemma, link, PoS=lp.PosTag.UNDEF, link_kind=None):
    return WordObj(lemma=lemma, pos_tag=PoS, parent_offs=link, synt_link=link_kind)


def _create_doc_obj_1():
    sents = [
        lp_doc.Sent(
            [
                _mkw('r', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
                _mkw('Ivanov', -1, lp.PosTag.PROPN, lp.SyntLink.NMOD),
                _mkw('I.', -1, lp.PosTag.PROPN, lp.SyntLink.FLAT),
                _mkw('V.', -1, lp.PosTag.PROPN, lp.SyntLink.FLAT),
                _mkw('verb', -4, lp.PosTag.VERB, lp.SyntLink.PARATAXIS),
                _mkw('cool', 2, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw('spam', 1, lp.PosTag.NOUN, lp.SyntLink.COMPOUND),
                _mkw('filter', -3, lp.PosTag.NOUN, lp.SyntLink.OBL),
            ]
        ),
    ]
    return lp_doc.Doc('id', sents=sents)


def test_add_mwes_to_doc_1():
    doc_obj = _create_doc_obj_1()
    add_phrases_to_doc(doc_obj, 4, min_cnt=0)

    words0 = list(doc_obj.sents())[0]
    assert not words0[0].mwes
    assert words0[1].mwes
    assert not words0[2].mwes
    assert not words0[3].mwes
    assert not words0[4].mwes
    assert not words0[5].mwes
    assert not words0[6].mwes
    assert words0[7].mwes
    mwe_phrase1 = words0[1].mwes[0]
    assert mwe_phrase1.get_str_repr() == 'Ivanov I. V.'
    mwe_phrase2 = words0[7].mwes[0]
    assert mwe_phrase2.get_str_repr() == 'spam filter'

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 4
    assert str_phrases == ['Ivanov I. V.', 'cool spam filter', 'r Ivanov I. V.', 'spam filter']


def test_add_mwes_to_doc_2():
    doc_obj = _create_doc_obj_1()
    add_phrases_to_doc(doc_obj, 3, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == ['Ivanov I. V.', 'cool spam filter', 'spam filter']


def test_add_mwes_to_doc_3():
    doc_obj = _create_doc_obj_1()
    words = list(doc_obj[0].words())
    # cool -> spam
    # spam is part of mwe
    words[-3].parent_offs = 1
    add_phrases_to_doc(doc_obj, 4, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == ['Ivanov I. V.', 'r Ivanov I. V.', 'spam filter']


def _create_doc_obj_2():
    sents = [
        lp_doc.Sent(
            [
                _mkw('long', 1, lp.PosTag.ADJ, lp.SyntLink.COMPOUND),
                _mkw('standing', 2, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw('spam', 1, lp.PosTag.NOUN, lp.SyntLink.COMPOUND),
                _mkw('filter', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
                _mkw('of', 2, lp.PosTag.ADP, lp.SyntLink.CASE),
                _mkw('web', 1, lp.PosTag.NOUN, lp.SyntLink.COMPOUND),
                _mkw('server', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
            ]
        ),
    ]
    return lp_doc.Doc('id', sents=sents)


def test_add_mwes_to_doc_4():
    doc_obj = _create_doc_obj_2()
    add_phrases_to_doc(doc_obj, 4, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 4
    assert str_phrases == [
        'long standing spam filter',
        'spam filter',
        'spam filter of web server',
        'web server',
    ]


def test_add_mwes_to_doc_5():
    doc_obj = _create_doc_obj_2()
    add_phrases_to_doc(doc_obj, 6, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 5
    assert str_phrases == [
        'long standing spam filter',
        'long standing spam filter of web server',
        'spam filter',
        'spam filter of web server',
        'web server',
    ]


@pytest.mark.timeout(0.8)
def test_large_mwe_1():
    words = [
        _mkw('r', 0, lp.PosTag.PROPN, lp.SyntLink.ROOT),
        _mkw('m1', -1, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m2', -1, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m3', -2, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m4', -3, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m5', -4, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m6', -5, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m7', -6, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m7.1', -7, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m8', -8, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m9', -9, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m10', -10, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m11', 3, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m12', 2, lp.PosTag.PROPN, lp.SyntLink.COMPOUND),
        _mkw('m13', 1, lp.PosTag.PROPN, lp.SyntLink.COMPOUND),
        _mkw('lr', -13, lp.PosTag.PROPN, lp.SyntLink.APPOS),
        _mkw('m15', -1, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m16', -2, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m17', -3, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m18', -4, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m19', -5, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m20', -6, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m21', -7, lp.PosTag.PROPN, lp.SyntLink.FLAT),
        _mkw('m22', 2, lp.PosTag.PROPN, lp.SyntLink.COMPOUND),
        _mkw('m23', 1, lp.PosTag.PROPN, lp.SyntLink.COMPOUND),
        _mkw('m24', -10, lp.PosTag.PROPN, lp.SyntLink.FLAT),
    ]
    doc_obj = lp_doc.Doc('id', sents=[lp_doc.Sent(words)])

    add_phrases_to_doc(doc_obj, 10, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 6
    assert str_phrases == [
        'm11 m12 m13 lr m15 m16 m17 m22 m23 m24',
        'm11 m12 m13 lr m15 m16 m18 m22 m23 m24',
        'm11 m12 m13 lr m15 m16 m19 m22 m23 m24',
        'r m1 m2 m3 m4 m5 m6 m7 m7.1 m10',
        'r m1 m2 m3 m4 m5 m6 m7 m7.1 m8',
        'r m1 m2 m3 m4 m5 m6 m7 m7.1 m9',
    ]


def test_mwe_with_conj_1():
    words = [
        _mkw('Red', 3, lp.PosTag.PROPN, lp.SyntLink.COMPOUND),
        _mkw('and', 1, lp.PosTag.CCONJ, lp.SyntLink.CC),
        _mkw('Blue', -2, lp.PosTag.PROPN, lp.SyntLink.CONJ),
        _mkw('Square', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
    ]
    doc_obj = lp_doc.Doc('id', sents=[lp_doc.Sent(words)])

    add_phrases_to_doc(doc_obj, 6, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 2
    assert str_phrases == [
        'Blue Square',
        'Red Square',
    ]


def test_mwe_propagate_prep_modifier_1():
    words = [
        _mkw('Red', 1, lp.PosTag.PROPN, lp.SyntLink.COMPOUND),
        _mkw('Square', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('of', 1, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw('temp', -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw('kek', -1, lp.PosTag.NOUN, lp.SyntLink.CONJ),
    ]
    doc_obj = lp_doc.Doc('id', sents=[lp_doc.Sent(words)])

    add_phrases_to_doc(doc_obj, 6, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == [
        'Red Square',
        'Red Square of kek',
        'Red Square of temp',
    ]


def test_mwe_propagate_prep_modifier_2():
    words = [
        _mkw('Root', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('of', 2, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw('spam', 1, lp.PosTag.NOUN, lp.SyntLink.COMPOUND),
        _mkw('filter', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw('other', -1, lp.PosTag.NOUN, lp.SyntLink.CONJ),
    ]
    doc_obj = lp_doc.Doc('id', sents=[lp_doc.Sent(words)])

    add_phrases_to_doc(doc_obj, 6, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == ['Root of other', 'Root of spam filter', 'spam filter']
