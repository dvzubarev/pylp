#!/usr/bin/env python
# coding: utf-8

import copy

from pylp.phrases.builder import Phrase
from pylp.phrases.util import replace_words_with_phrases, add_phrases_to_doc, make_phrases
import pylp.common as lp


def _mkw(num, link, PoS=lp.PosTag.UNDEF, link_kind=-1):
    word_obj = {lp.Attr.WORD_NUM: num, lp.Attr.SYNTAX_PARENT: link}
    if PoS != lp.PosTag.UNDEF:
        word_obj[lp.Attr.POS_TAG] = PoS
    if link_kind != lp.SyntLink.ROOT:
        word_obj[lp.Attr.SYNTAX_LINK_NAME] = link_kind
    return word_obj


def _create_doc_obj():
    doc_obj = {
        'words': ['h1', 'of', 'm1', 'h2', 'm2', 'h3'],
        'sents': [
            [
                _mkw(0, 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
                _mkw(1, 2, lp.PosTag.ADP, lp.SyntLink.CASE),
                _mkw(2, 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw(3, -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
            ],
            [
                _mkw(2, 2, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw(4, 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
                _mkw(3, 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
            ],
            [
                _mkw(0, 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
                _mkw(1, 1, lp.PosTag.ADP, lp.SyntLink.CASE),
                _mkw(5, -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
            ],
        ],
    }
    return doc_obj


def _p2str(phrase, with_phrases=False):
    return '_'.join(phrase.get_words(with_phrases))


def test_add_phrases_to_doc():
    doc_obj = _create_doc_obj()
    add_phrases_to_doc(doc_obj, 4, use_words=True, min_cnt=0)
    sent_phrases = doc_obj['sent_phrases']

    assert len(sent_phrases) == 3
    sent0 = sent_phrases[0]
    str_phrases = [_p2str(p, with_phrases=True) for p in sent0]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == ['h1_of_h2', 'h1_of_m1_h2', 'm1_h2']

    sent1 = sent_phrases[1]
    str_phrases = [_p2str(p) for p in sent1]
    str_phrases.sort()
    assert len(str_phrases) == 3
    assert str_phrases == ['m1_h2', 'm1_m2_h2', 'm2_h2']

    sent2 = sent_phrases[2]
    str_phrases = [_p2str(p, True) for p in sent2]
    str_phrases.sort()
    assert len(str_phrases) == 1
    assert str_phrases == ['h1_of_h3']


def test_add_phrases_to_doc_with_min_cnt():
    doc_obj = _create_doc_obj()
    add_phrases_to_doc(doc_obj, 4, use_words=True, min_cnt=2)
    sent_phrases = doc_obj['sent_phrases']

    assert len(sent_phrases) == 3
    sent0 = sent_phrases[0]
    str_phrases = [_p2str(p) for p in sent0]
    str_phrases.sort()
    assert len(str_phrases) == 1
    assert str_phrases == ['m1_h2']

    sent1 = sent_phrases[1]
    str_phrases = [_p2str(p) for p in sent1]
    str_phrases.sort()
    assert len(str_phrases) == 1
    assert str_phrases == ['m1_h2']

    sent2 = sent_phrases[2]
    str_phrases = [_p2str(p) for p in sent2]
    str_phrases.sort()
    assert len(str_phrases) == 0


def test_replace():
    words = ['r', 'm1', 'h1', 'h2']
    sent = [
        _mkw(0, 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw(1, 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw(2, -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw(3, -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    phrases = make_phrases(sent, words, 3)
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
