#!/usr/bin/env python
# coding: utf-8

import pytest

from ex_pylp.common import Attr
from ex_pylp.post_processors import FragmentsMaker


@pytest.fixture
def fragments_maker():
    return FragmentsMaker()


def test_basic(fragments_maker):
    doc = {
        'sents': [
            ['skip'],
            ['good', 'sent'],
            ['another', 'good', 'sent1'],
            ['another', 'good', 'sent2'],
            ['skip'],
            ['skip'],
            ['another', 'good', 'sent3'],
            ['new', 'fragment'],
            ['with', 'overlap'],
            ['another', 'good', 'sent4'],
            ['skip'],
            ['another', 'good', 'sent5'],
        ]
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 0,
                    min_sent_length = 2, overlap = 2)

    fragments = doc['fragments']
    print(doc)
    assert len(fragments)  == 3
    assert fragments[0] == (0, 6)
    assert fragments[1] == (3, 8)
    assert fragments[2] == (7, 11)


def test_empty(fragments_maker):
    doc = {
        'sents': []
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 0,
                    min_sent_length = 2, overlap = 2)

    assert not doc['fragments']

def test_many_skips(fragments_maker):

    doc = {
        'sents': [
            ['skip'],
            ['skip'],
            ['skip'],
            ['skip'],
            ['skip'],
        ]
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 0,
                    min_sent_length = 2, overlap = 2)
    assert len(doc['fragments']) == 1
    assert doc['fragments'][0] == (0, 4)

def test_short(fragments_maker):
    doc = {
        'sents': [
            ['skip'],
            ['good', 'sent'],
            ['another', 'good', 'sent1'],
        ]
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 0,
                    min_sent_length = 2, overlap = 2)

    fragments = doc['fragments']
    print(doc)
    assert len(fragments)  == 1
    assert fragments[0] == (0, 2)

def test_no_overlap(fragments_maker):
    doc = {
        'sents': [
            ['skip'],
            ['good', 'sent'],
            ['another', 'good', 'sent1'],
            ['another', 'good', 'sent2'],
            ['skip'],
            ['skip'],
            ['another', 'good', 'sent3'],
            ['new', 'fragment'],
            ['with', 'overlap'],
            ['another', 'good', 'sent4'],
            ['skip'],
            ['another', 'good', 'sent5'],
        ]
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 0,
                    min_sent_length = 2, overlap = 0)

    fragments = doc['fragments']
    print(doc)
    assert len(fragments)  == 2
    assert fragments[0] == (0, 6)
    assert fragments[1] == (7, 11)

def test_max_chars(fragments_maker):
    doc = {
        'words': ['normal',
                  'sentence',
                  'here',
                  'a' * 100],
        'sents': [
            [{Attr.WORD_NUM: 0}, {Attr.WORD_NUM: 1}, {Attr.WORD_NUM: 2}],
            [{Attr.WORD_NUM: 3}],
            [{Attr.WORD_NUM: 3}],
            [{Attr.WORD_NUM: 0}, {Attr.WORD_NUM: 1}, {Attr.WORD_NUM: 2}],
            [{Attr.WORD_NUM: 0}, {Attr.WORD_NUM: 1}, {Attr.WORD_NUM: 2}],
        ]
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 20,
                    min_sent_length = 2, overlap = 0)

    fragments = doc['fragments']
    assert len(fragments)  == 3
    assert fragments[0] == (0, 1)
    assert fragments[1] == (2, 2)
    assert fragments[2] == (3, 4)

    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 40,
                    min_sent_length = 2, overlap = 2)

    fragments = doc['fragments']
    assert len(fragments)  == 3
    assert fragments[0] == (0, 1)
    assert fragments[1] == (2, 2)
    assert fragments[2] == (3, 4)


    doc = {
        'words': ['normal',
                  'sentence',
                  'here',
                  'a' * 100],
        'sents': [
            [{Attr.WORD_NUM: 3}],
            [{Attr.WORD_NUM: 0}, {Attr.WORD_NUM: 1}, {Attr.WORD_NUM: 2}],
            [{Attr.WORD_NUM: 0}, {Attr.WORD_NUM: 1}, {Attr.WORD_NUM: 2}],
        ]
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 40,
                    min_sent_length = 2, overlap = 2)

    fragments = doc['fragments']
    assert len(fragments) == 2

def test_overlap_at_the_end(fragments_maker):
    doc = {
        'sents': [
            ['another', 'good', 'sent1'],
            ['another', 'good', 'sent2'],
            ['another', 'good', 'sent3'],
            ['another', 'good', 'sent4'],
            ['another', 'good', 'sent5'],
            ['another', 'good', 'sent6'],
            ['another', 'good', 'sent7'],
            ['another', 'good', 'sent8'],
        ]
    }
    fragments_maker('', doc, max_fragment_length = 4, max_chars_cnt = 0,
                    min_sent_length = 2, overlap = 2)

    fragments = doc['fragments']
    print(doc)
    assert len(fragments)  == 3
    assert fragments[0] == (0, 3)
    assert fragments[1] == (2, 5)
    assert fragments[2] == (4, 7)
