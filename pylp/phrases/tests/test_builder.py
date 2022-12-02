#!/usr/bin/env python
# coding: utf-8

import copy
import logging

from pylp.phrases.phrase import Phrase
from pylp.phrases.builder import (
    BasicPhraseBuilder,
    PhraseBuilder,
    make_new_phrase,
)

import pylp.common as lp
from pylp.word_obj import WordObj
from pylp import lp_doc


class _TestPhraseBuilder(BasicPhraseBuilder):
    def _test_modifier(self, word_obj: WordObj, pos, sent, mods_index):
        return bool(word_obj.parent_offs)

    def _test_head(self, word_obj: WordObj, pos, sent, mods_index):
        return word_obj.parent_offs is not None


def _mkw(lemma, link, PoS=lp.PosTag.UNDEF, link_kind=None):
    return WordObj(lemma=lemma, pos_tag=PoS, parent_offs=link, synt_link=link_kind)


def _create_sent():
    words = [
        _mkw('известный', 0),  # 0
        _mkw('43', 0),
        _mkw('клинический', 1),
        _mkw('случай', 0),
        _mkw('психоаналитический', 1),
        _mkw('практика', 0),
        _mkw('зигмунд', 1),  # 6
        _mkw('фрейд', -2),
        _mkw('весь', 0),
        _mkw('этот', 0),
        _mkw('работа', 0),  # 10
    ]
    return lp_doc.Sent(words)


def _create_complex_sent():
    words = [
        _mkw('m1', 2),
        _mkw('m2', 1),
        _mkw('r', 0),
        _mkw('m3', 1),
        _mkw('h1', -2),
        _mkw('m4', 2),
        _mkw('m5', 1),
        _mkw('h2', -3),
    ]
    return lp_doc.Sent(words)


def _p2str(phrase):
    return '_'.join(phrase.get_words())


def test_phrases_builder():
    sent = _create_sent()
    phrase_builder = _TestPhraseBuilder(MaxN=2)

    phrases = phrase_builder.build_phrases_for_sent(sent)
    assert len(phrases) == 4
    str_phrases = [_p2str(p) for p in phrases]
    str_phrases.sort()
    assert str_phrases == [
        'зигмунд_фрейд',
        'клинический_случай',
        'практика_фрейд',
        'психоаналитический_практика',
    ]

    phrase_builder = _TestPhraseBuilder(MaxN=3)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [_p2str(p) for p in phrases]
    str_phrases.sort()
    # print(str_phrases)
    assert len(phrases) == 6
    assert str_phrases == [
        'зигмунд_фрейд',
        'клинический_случай',
        'практика_зигмунд_фрейд',
        'практика_фрейд',
        'психоаналитический_практика',
        'психоаналитический_практика_фрейд',
    ]

    phrase_builder = _TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [_p2str(p) for p in phrases]
    str_phrases.sort()
    # print(str_phrases)
    assert len(phrases) == 7
    assert str_phrases == [
        'зигмунд_фрейд',
        'клинический_случай',
        'практика_зигмунд_фрейд',
        'практика_фрейд',
        'психоаналитический_практика',
        'психоаналитический_практика_зигмунд_фрейд',
        'психоаналитический_практика_фрейд',
    ]


def test_phrases_builder_2():
    sent = _create_complex_sent()
    phrase_builder = _TestPhraseBuilder(MaxN=3)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [_p2str(p) for p in phrases]
    str_phrases.sort()
    # print(str_phrases)
    assert len(phrases) == 16
    etal_phrases = [
        'h1_h2',
        'h1_m4_h2',
        'h1_m5_h2',
        'm1_m2_r',
        'm1_r',
        'm1_r_h1',
        'm2_r',
        'm2_r_h1',
        'm3_h1',
        'm3_h1_h2',
        'm4_h2',
        'm4_m5_h2',
        'm5_h2',
        'r_h1',
        'r_h1_h2',
        'r_m3_h1',
    ]
    assert str_phrases == etal_phrases

    phrase_builder = _TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [_p2str(p) for p in phrases]
    str_phrases.sort()
    # print(str_phrases)
    assert len(phrases) == 27
    etal_phrases.extend(
        [
            'm1_r_h1_h2',
            'm1_r_m3_h1',
            'm1_m2_r_h1',
            'm2_r_h1_h2',
            'm2_r_m3_h1',
            'r_h1_m4_h2',
            'r_h1_m5_h2',
            'r_m3_h1_h2',
            'h1_m4_m5_h2',
            'm3_h1_m4_h2',
            'm3_h1_m5_h2',
        ]
    )
    etal_phrases.sort()
    assert str_phrases == etal_phrases


def test_multiple_right_mods():
    sent = lp_doc.Sent([_mkw('r', 0), _mkw('m1', 1), _mkw('h1', -2), _mkw('h2', -3)])

    phrase_builder = _TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [_p2str(p) for p in phrases]
    str_phrases.sort()
    # print (str_phrases)

    assert len(phrases) == 6
    assert str_phrases == ['m1_h1', 'r_h1', 'r_h1_h2', 'r_h2', 'r_m1_h1', 'r_m1_h1_h2']


def test_phrase_merging1():
    sent = lp_doc.Sent([_mkw('m1', 1), _mkw('r', 0), _mkw('m2', 1), _mkw('h1', -2)])

    root = Phrase.from_word(1, sent[1])
    mod1 = Phrase.from_word(0, sent[0])

    root = make_new_phrase(root, mod1, sent, set())
    assert root is not None
    assert len(root.get_words()) == 2
    assert root.get_words() == ['m1', 'r']
    assert root.get_deps() == [1, 0]

    root_m1_r = copy.deepcopy(root)

    head1 = Phrase.from_word(3, sent[3])
    root = make_new_phrase(root, head1, sent, set())
    assert root is not None
    assert len(root.get_words()) == 3
    assert root.get_words() == ['m1', 'r', 'h1']
    assert root.get_deps() == [1, 0, -1]

    root = copy.deepcopy(root_m1_r)
    mod2 = Phrase.from_word(2, sent[2])
    head1 = make_new_phrase(head1, mod2, sent, set())
    assert head1 is not None
    root = make_new_phrase(root, head1, sent, set())
    assert root is not None
    assert len(root.get_words()) == 4
    assert root.get_words() == ['m1', 'r', 'm2', 'h1']
    assert root.get_deps() == [1, 0, 1, -2]


def test_phrase_merging2():
    sent = lp_doc.Sent([_mkw('r', 0), _mkw('m1', 1), _mkw('h1', -2), _mkw('h2', -3)])

    root = Phrase.from_word(0, sent[0])
    mod1 = Phrase.from_word(1, sent[1])
    h1 = Phrase.from_word(2, sent[2])
    h2 = Phrase.from_word(3, sent[3])
    root = make_new_phrase(root, h2, sent, set())
    assert root is not None
    assert root.get_words() == ['r', 'h2']
    assert root.get_deps() == [0, -1]
    mod = make_new_phrase(h1, mod1, sent, set())
    root = make_new_phrase(root, mod, sent, set())
    assert root is not None
    assert len(root.get_words()) == 4
    assert root.get_words() == ['r', 'm1', 'h1', 'h2']
    assert root.get_deps() == [0, 1, -2, -3]


def test_phrase_merging3():
    sent = lp_doc.Sent([_mkw('m1', 2), _mkw('m2', 1), _mkw('r', 0)])
    root = Phrase.from_word(2, sent[2])
    mod1 = Phrase.from_word(0, sent[0])
    mod2 = Phrase.from_word(1, sent[1])
    root = make_new_phrase(root, mod1, sent, set())
    assert root is not None
    assert root.get_head_pos() == 1
    root = make_new_phrase(root, mod2, sent, set())
    assert root is not None
    assert len(root.get_words()) == 3
    assert root.get_words() == ['m1', 'm2', 'r']
    assert root.get_deps() == [2, 1, 0]


def test_undefined_words():
    sent = lp_doc.Sent([_mkw('r', 0), _mkw(None, None), _mkw('h1', -2), _mkw(None, None)])

    phrase_builder = _TestPhraseBuilder(MaxN=5)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [_p2str(p) for p in phrases]
    assert len(phrases) == 1
    assert str_phrases == ['r_h1']


def test_full_phrase_builder():
    words = [
        _mkw('r', 0, lp.PosTag.VERB, lp.SyntLink.ROOT),
        _mkw('m1', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('h1', 1, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw('h2', -3, lp.PosTag.NOUN, lp.SyntLink.NSUBJ),
    ]
    sent = lp_doc.Sent(words)

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [_p2str(p) for p in phrases]
    str_phrases.sort()
    assert len(phrases) == 3
    assert str_phrases == ['h1_h2', 'm1_h1', 'm1_h1_h2']

    str_phrases = [p.get_str_repr() for p in phrases]
    str_phrases.sort()
    assert len(phrases) == 3
    assert str_phrases == ['h1 h2', 'm1 h1', 'm1 h1 h2']


def test_phrases_with_prepositions():
    words = [
        _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('of', 2, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw('m1', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('h2', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [p.get_str_repr() for p in phrases]
    str_phrases.sort()
    assert len(phrases) == 3
    assert str_phrases == ['h1 of h2', 'h1 of m1 h2', 'm1 h2']


def test_phrases_with_prepositions_1():
    words = [
        _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('к', 1, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw('h2', -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [p.get_str_repr() for p in phrases]
    str_phrases.sort()
    assert len(phrases) == 1
    assert str_phrases == ['h1 к h2']


def test_phrases_with_prepositions_2():
    words = [
        _mkw('r', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('h1', -1, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw('от', 1, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw('h2', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    str_phrases = [p.get_str_repr() for p in phrases]
    str_phrases.sort()
    assert len(phrases) == 3
    assert str_phrases == ['r h1', 'r h1 от h2', 'r от h2']


def test_phrase_id():
    words = [
        _mkw('m1', 2, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('m2', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('r', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
    ]
    sent = lp_doc.Sent(words)

    phrase_builder = PhraseBuilder(MaxN=3)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    phrase_id = [p.get_id() for p in phrases if p.size() == 3][0]
    assert phrase_id == 16874608482926624595

    words = [
        _mkw('m2', 2, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('m1', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('r', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
    ]
    sent = lp_doc.Sent(words)

    phrases = phrase_builder.build_phrases_for_sent(sent)
    phrase_id2 = [p.get_id() for p in phrases if p.size() == 3][0]
    assert phrase_id == phrase_id2


def test_phrase_id2():
    words = [
        _mkw('r', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('m1', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('h1', -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw('h2', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    phrase_id = [p.get_id() for p in phrases if p.size() == 4][0]
    assert phrase_id == 536335079326450557

    words = [
        _mkw('r', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('h2', -1, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw('m1', 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw('h1', -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)

    phrases2 = phrase_builder.build_phrases_for_sent(sent)
    phrase_id2 = [p.get_id() for p in phrases2 if p.size() == 4][0]
    assert phrase_id == phrase_id2


def test_phrase_id_with_prepositions():
    words = [
        _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('of', 1, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw('h2', -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    assert len(phrases) == 1
    phrase_id = phrases[0].get_id()
    assert phrase_id == 1999309033942072342

    words = [
        _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('h2', -1, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)

    phrases = phrase_builder.build_phrases_for_sent(sent)
    assert len(phrases) == 1
    phrase_id2 = phrases[0].get_id()
    assert phrase_id != phrase_id2


def test_overlap():
    sent = _create_complex_sent()
    phrase_builder = _TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    r_h1_m5_h2 = None
    r_h1_m4_h2 = None
    h1_m4_h2 = None
    m4_h2 = None
    h1_h2 = None
    for p in phrases:
        pstr = _p2str(p)
        if pstr == "r_h1_m5_h2":
            r_h1_m5_h2 = p
        elif pstr == "r_h1_m4_h2":
            r_h1_m4_h2 = p
        elif pstr == "h1_m4_h2":
            h1_m4_h2 = p
        elif pstr == "m4_h2":
            m4_h2 = p
        elif pstr == "h1_h2":
            h1_h2 = p

    assert r_h1_m4_h2 is not None
    assert r_h1_m5_h2 is not None
    assert h1_m4_h2 is not None
    assert m4_h2 is not None
    assert h1_h2 is not None
    assert r_h1_m4_h2.intersects(r_h1_m5_h2)
    assert r_h1_m5_h2.intersects(r_h1_m4_h2)
    assert r_h1_m4_h2.overlaps(r_h1_m5_h2)
    assert r_h1_m5_h2.overlaps(r_h1_m4_h2)
    assert r_h1_m4_h2.overlaps(h1_m4_h2)
    assert not h1_m4_h2.overlaps(r_h1_m4_h2)
    assert h1_m4_h2.overlaps(h1_h2)
    assert h1_h2.overlaps(h1_m4_h2)
    assert not h1_h2.overlaps(r_h1_m4_h2)
    assert h1_h2.intersects(r_h1_m4_h2)
    assert m4_h2.intersects(h1_h2)
    assert not m4_h2.overlaps(h1_h2)
    assert h1_m4_h2.overlaps(m4_h2)
    assert not m4_h2.overlaps(h1_m4_h2)


def test_contains():
    sent = _create_complex_sent()
    phrase_builder = _TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    r_h1_m5_h2 = None
    r_h1_m4_h2 = None
    h1_m4_h2 = None
    m4_h2 = None
    h1_h2 = None
    for p in phrases:
        pstr = _p2str(p)
        if pstr == "r_h1_m5_h2":
            r_h1_m5_h2 = p
        elif pstr == "r_h1_m4_h2":
            r_h1_m4_h2 = p
        elif pstr == "h1_m4_h2":
            h1_m4_h2 = p
        elif pstr == "m4_h2":
            m4_h2 = p
        elif pstr == "h1_h2":
            h1_h2 = p

    assert r_h1_m4_h2 is not None
    assert r_h1_m5_h2 is not None
    assert h1_m4_h2 is not None
    assert m4_h2 is not None
    assert h1_h2 is not None

    assert not r_h1_m4_h2.contains(r_h1_m5_h2)
    assert not r_h1_m5_h2.contains(r_h1_m4_h2)
    assert not r_h1_m5_h2.contains(h1_m4_h2)
    assert r_h1_m4_h2.contains(h1_m4_h2)
    assert r_h1_m4_h2.contains(h1_h2)
    assert r_h1_m5_h2.contains(h1_h2)
    assert h1_m4_h2.contains(h1_h2)
    assert not r_h1_m5_h2.contains(m4_h2)
    assert r_h1_m4_h2.contains(m4_h2)
    assert not m4_h2.contains(h1_m4_h2)
    assert not m4_h2.contains(r_h1_m4_h2)
    assert m4_h2.contains(m4_h2)
