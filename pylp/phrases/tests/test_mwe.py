#!/usr/bin/env python3

from pylp import lp_doc

from pylp.phrases.builder import Phrase
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
    assert words0[0].mwe is None
    assert words0[1].mwe is not None
    assert words0[2].mwe is None
    assert words0[3].mwe is None
    assert words0[4].mwe is None
    assert words0[5].mwe is None
    assert words0[6].mwe is None
    assert words0[7].mwe is not None
    mwe_phrase1 = words0[1].mwe
    assert mwe_phrase1.get_str_repr() == 'Ivanov I. V.'
    mwe_phrase2 = words0[7].mwe
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
