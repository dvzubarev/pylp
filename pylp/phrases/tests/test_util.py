#!/usr/bin/env python
# coding: utf-8

import copy
from pylp import lp_doc

from pylp.phrases.builder import Phrase
from pylp.phrases.util import replace_words_with_phrases, add_phrases_to_doc, make_phrases
import pylp.common as lp
from pylp.word_obj import WordObj


def _mkw(lemma, link, PoS=lp.PosTag.UNDEF, link_kind=None):
    return WordObj(lemma=lemma, pos_tag=PoS, parent_offs=link, synt_link=link_kind)


def _create_doc_obj():
    sents = [
        lp_doc.Sent(
            [
                _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
                _mkw('of', 2, lp.PosTag.ADP, lp.SyntLink.CASE),
                _mkw('m1', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw('h2', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
            ]
        ),
        lp_doc.Sent(
            [
                _mkw('m1', 2, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw('m2', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw('h2', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
            ]
        ),
        lp_doc.Sent(
            [
                _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
                _mkw('of', 1, lp.PosTag.ADP, lp.SyntLink.CASE),
                _mkw('h3', -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
            ]
        ),
    ]

    return lp_doc.Doc('id', sents=sents)


def _p2str(phrase):
    return '_'.join(phrase.get_words())


def test_add_phrases_to_doc():
    doc_obj = _create_doc_obj()
    add_phrases_to_doc(doc_obj, 4, min_cnt=0)

    sent0 = doc_obj[0]
    str_phrases = [p.get_str_repr() for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == ['h1 of h2', 'h1 of m1 h2', 'm1 h2']

    sent1 = doc_obj[1]
    str_phrases = [p.get_str_repr() for p in sent1.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == ['m1 h2', 'm1 m2 h2', 'm2 h2']

    sent2 = doc_obj[2]
    str_phrases = [p.get_str_repr() for p in sent2.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 1
    assert str_phrases == ['h1 of h3']


def test_add_phrases_to_doc_with_min_cnt():
    doc_obj = _create_doc_obj()
    add_phrases_to_doc(doc_obj, 4, min_cnt=2)

    sent0 = doc_obj[0]
    str_phrases = [_p2str(p) for p in sent0.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 1
    assert str_phrases == ['m1_h2']

    sent1 = doc_obj[1]
    str_phrases = [_p2str(p) for p in sent1.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 1
    assert str_phrases == ['m1_h2']

    sent2 = doc_obj[2]
    str_phrases = [_p2str(p) for p in sent2.phrases()]
    str_phrases.sort()
    assert len(str_phrases) == 0


def test_replace():
    sent = lp_doc.Sent(
        [
            _mkw('r', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
            _mkw('m1', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
            _mkw('h1', -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
            _mkw('h2', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        ]
    )
    words = ['r', 'm1', 'h1', 'h2']

    phrases = make_phrases(sent, 3)
    sent_words = copy.copy(words)
    new_sent = replace_words_with_phrases(sent_words, phrases)
    print(phrases)
    print(new_sent)
    assert len(new_sent) == 2
    sent_phrases = [_p2str(p) for p in new_sent]
    sent_phrases.sort()
    assert sent_phrases == ['r_h1_h2', 'r_m1_h1']

    new_sent = replace_words_with_phrases(sent_words, phrases, allow_overlapping_phrases=False)
    assert len(new_sent) == 2
    sent_phrases = [_p2str(p) if isinstance(p, Phrase) else p for p in new_sent]
    assert sent_phrases == ['r_m1_h1', 'h2']

    new_sent = replace_words_with_phrases(
        sent_words, phrases, allow_overlapping_phrases=False, keep_filler=True
    )
    assert len(new_sent) == 4
    sent_phrases = [_p2str(p) if isinstance(p, Phrase) else p for p in new_sent]
    assert sent_phrases == ['r_m1_h1', None, None, 'h2']
