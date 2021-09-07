#!/usr/bin/env python
# coding: utf-8

import copy
import logging

from pylp.phrases.builder import (
    BasicPhraseBuilder,
    PhraseBuilder,
    Phrase,
    Sent,
    make_new_phrase,
    make_2word_phrase,
)

import pylp.common as lp


class TestPhraseBuilder(BasicPhraseBuilder):
    def _test_modifier(self, word_obj, pos, sent, mods_index):
        return lp.Attr.SYNTAX_PARENT in word_obj and word_obj[lp.Attr.SYNTAX_PARENT]

    def _test_head(self, word_obj, pos, sent, mods_index):
        return True


def _mkw(num, link, PoS=lp.PosTag.UNDEF, link_kind=-1):
    word_obj = {lp.Attr.WORD_NUM: num, lp.Attr.SYNTAX_PARENT: link}
    if PoS != lp.PosTag.UNDEF:
        word_obj[lp.Attr.POS_TAG] = PoS
    if link_kind != lp.SyntLink.ROOT:
        word_obj[lp.Attr.SYNTAX_LINK_NAME] = link_kind
    return word_obj


def _create_sent():
    words = [
        'известный',  # 0
        '43',
        'клинический',
        'случай',
        'психоаналитический',
        'практика',
        'зигмунд',  # 6
        'фрейд',
        'весь',
        'этот',
        'работа',  # 10
    ]
    sent = [
        _mkw(0, 0),
        _mkw(1, 0),
        _mkw(2, 1),
        _mkw(3, 0),
        _mkw(4, 1),
        _mkw(5, 0),
        _mkw(6, 1),
        _mkw(7, -2),
        _mkw(8, 0),
        _mkw(9, 0),
        _mkw(10, 0),
    ]

    return sent, words


def _create_complex_sent():
    # fmt: off
    words = [
        'm1',
        'm2',
        'r', #2
        'm3',
        'h1', #4
        'm4',
        'm5',
        'h2' #7
    ]
    # fmt: on

    sent = [
        _mkw(0, 2),
        _mkw(1, 1),
        _mkw(2, 0),
        _mkw(3, 1),
        _mkw(4, -2),
        _mkw(5, 2),
        _mkw(6, 1),
        _mkw(7, -3),
    ]
    return sent, words


def test_phrases_builder():
    sent, words = _create_sent()
    phrase_builder = TestPhraseBuilder(MaxN=2)

    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    assert len(phrases) == 4
    str_phrases = [p.get_id() for p in phrases]
    str_phrases.sort()
    assert str_phrases == [
        'зигмунд_фрейд',
        'клинический_случай',
        'практика_фрейд',
        'психоаналитический_практика',
    ]

    phrase_builder = TestPhraseBuilder(MaxN=3)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
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

    phrase_builder = TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
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
    sent, words = _create_complex_sent()
    phrase_builder = TestPhraseBuilder(MaxN=3)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
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

    phrase_builder = TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
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
    words = ['r', 'm1', 'h1', 'h2']
    sent = [_mkw(0, 0), _mkw(1, 1), _mkw(2, -2), _mkw(3, -3)]

    phrase_builder = TestPhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
    str_phrases.sort()
    # print (str_phrases)

    assert len(phrases) == 6
    assert str_phrases == ['m1_h1', 'r_h1', 'r_h1_h2', 'r_h2', 'r_m1_h1', 'r_m1_h1_h2']


def test_phrase_merging1():
    sent = Sent([_mkw(0, 1), _mkw(1, 0), _mkw(2, 1), _mkw(3, -2)], ['m1', 'r', 'm2', 'h1'])

    root = Phrase(1, sent)
    mod1 = Phrase(0, sent)

    root = make_new_phrase(root, mod1, sent, set())

    assert len(root.get_words()) == 2
    assert root.get_words() == ['m1', 'r']
    assert root.get_deps() == [1, None]
    assert root.get_id() == 'm1_r'

    root_m1_r = copy.deepcopy(root)

    head1 = Phrase(3, sent)
    root = make_new_phrase(root, head1, sent, set())
    assert len(root.get_words()) == 3
    assert root.get_words() == ['m1', 'r', 'h1']
    assert root.get_deps() == [1, None, -1]
    assert root.get_id() == 'm1_r_h1'

    root = copy.deepcopy(root_m1_r)
    mod2 = Phrase(2, sent)
    head1 = make_new_phrase(head1, mod2, sent, set())
    root = make_new_phrase(root, head1, sent, set())
    assert len(root.get_words()) == 4
    assert root.get_words() == ['m1', 'r', 'm2', 'h1']
    assert root.get_deps() == [1, None, 1, -2]
    assert root.get_id() == 'm1_r_m2_h1'


def test_phrase_merging2():
    sent = Sent([_mkw(0, 0), _mkw(1, 1), _mkw(2, -2), _mkw(3, -3)], ['r', 'm1', 'h1', 'h2'])

    root = Phrase(0, sent)
    mod1 = Phrase(1, sent)
    h1 = Phrase(2, sent)
    h2 = Phrase(3, sent)
    root = make_2word_phrase(root, h2, sent)
    assert root.get_id() == 'r_h2'
    assert root.get_deps() == [None, -1]
    mod = make_2word_phrase(h1, mod1, sent)
    root = make_new_phrase(root, mod, sent, set())
    assert len(root.get_words()) == 4
    assert root.get_words() == ['r', 'm1', 'h1', 'h2']
    assert root.get_deps() == [None, 1, -2, -3]
    assert root.get_id() == 'r_m1_h1_h2'


def test_phrase_merging3():
    sent = Sent([_mkw(0, 2), _mkw(1, 1), _mkw(2, 0)], ['m1', 'm2', 'r'])
    root = Phrase(2, sent)
    mod1 = Phrase(0, sent)
    mod2 = Phrase(1, sent)
    root = make_2word_phrase(root, mod1, sent)
    assert root.get_head_pos() == 1
    root = make_new_phrase(root, mod2, sent, set())
    assert len(root.get_words()) == 3
    assert root.get_words() == ['m1', 'm2', 'r']
    assert root.get_deps() == [2, 1, None]
    assert root.get_id() == 'm1_m2_r'


def test_excluding_words():
    words = ['r', 'm1', 'h1', 'h2']
    sent = [_mkw(0, 0), _mkw(lp.UNDEF_WORD_NUM, 1), _mkw(2, -2), _mkw(lp.UNDEF_WORD_NUM, -3)]

    phrase_builder = TestPhraseBuilder(MaxN=5)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
    assert len(phrases) == 1
    assert str_phrases == ['r_h1']


def test_full_phrase_builder():
    words = ['r', 'm1', 'h1', 'h2']
    sent = [
        _mkw(0, 0, lp.PosTag.VERB, lp.SyntLink.ROOT),
        _mkw(1, 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw(2, 1, lp.PosTag.NOUN, lp.SyntLink.NMOD),
        _mkw(3, -3, lp.PosTag.NOUN, lp.SyntLink.NSUBJ),
    ]

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
    str_phrases.sort()
    assert len(phrases) == 3
    assert str_phrases == ['h1_h2', 'm1_h1', 'm1_h1_h2']


def test_phrases_with_prepositions():
    words = ['h1', 'of', 'm1', 'h2']
    sent = [
        _mkw(0, 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw(1, 2, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw(2, 1, lp.PosTag.ADJ, lp.SyntLink.AMOD),
        _mkw(3, -3, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]

    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent, words)
    str_phrases = [p.get_id() for p in phrases]
    str_phrases.sort()
    assert len(phrases) == 3
    assert str_phrases == ['h1_of_h2', 'h1_of_m1_h2', 'm1_h2']
