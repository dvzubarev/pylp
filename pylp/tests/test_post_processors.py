#!/usr/bin/env python
# coding: utf-8

import pytest

from pylp.post_processors import FragmentsMaker
from pylp import lp_doc
from pylp.word_obj import WordObj


@pytest.fixture
def fragments_maker():
    return FragmentsMaker()


def _make_doc_obj(sents):
    doc = lp_doc.Doc('id')
    for s in sents:
        doc.add_sent(s)
    return doc


def test_basic(fragments_maker):
    doc = _make_doc_obj(
        [
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
    )
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=0, min_sent_length=2, overlap=2)

    fragments = doc.get_fragments()
    print(doc)
    assert fragments is not None
    assert len(fragments) == 3
    assert fragments[0] == (0, 6)
    assert fragments[1] == (3, 8)
    assert fragments[2] == (7, 11)


def test_empty(fragments_maker):
    doc = _make_doc_obj([])
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=0, min_sent_length=2, overlap=2)

    assert not doc.get_fragments()


def test_many_skips(fragments_maker):
    doc = _make_doc_obj(
        [
            ['skip'],
            ['skip'],
            ['skip'],
            ['skip'],
            ['skip'],
        ]
    )
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=0, min_sent_length=2, overlap=2)
    fragments = doc.get_fragments()
    assert fragments is not None
    assert len(fragments) == 1
    assert fragments[0] == (0, 4)


def test_short(fragments_maker):
    doc = _make_doc_obj(
        [
            ['skip'],
            ['good', 'sent'],
            ['another', 'good', 'sent1'],
        ]
    )
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=0, min_sent_length=2, overlap=2)

    fragments = doc.get_fragments()
    print(doc)
    assert fragments is not None
    assert len(fragments) == 1
    assert fragments[0] == (0, 2)


def test_no_overlap(fragments_maker):
    doc = _make_doc_obj(
        [
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
    )
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=0, min_sent_length=2, overlap=0)

    fragments = doc.get_fragments()
    print(doc)
    assert fragments is not None
    assert len(fragments) == 2
    assert fragments[0] == (0, 6)
    assert fragments[1] == (7, 11)


def test_max_chars(fragments_maker):
    word1 = WordObj(lemma='normal')
    word2 = WordObj(lemma='sentence')
    word3 = WordObj(lemma='here')
    word4 = WordObj(lemma='a' * 100)
    doc = _make_doc_obj(
        [[word1, word2, word3], [word4], [word4], [word1, word2, word3], [word1, word2, word3]]
    )
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=20, min_sent_length=2, overlap=0)

    fragments = doc.get_fragments()
    assert fragments is not None
    assert len(fragments) == 3
    assert fragments[0] == (0, 1)
    assert fragments[1] == (2, 2)
    assert fragments[2] == (3, 4)

    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=40, min_sent_length=2, overlap=2)

    fragments = doc.get_fragments()
    assert fragments is not None
    assert len(fragments) == 3
    assert fragments[0] == (0, 1)
    assert fragments[1] == (2, 2)
    assert fragments[2] == (3, 4)

    doc = _make_doc_obj([[word4], [word1, word2, word3], [word1, word2, word3]])
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=40, min_sent_length=2, overlap=2)

    fragments = doc.get_fragments()
    assert fragments is not None
    assert len(fragments) == 2


def test_overlap_at_the_end(fragments_maker):
    doc = _make_doc_obj(
        [
            ['another', 'good', 'sent1'],
            ['another', 'good', 'sent2'],
            ['another', 'good', 'sent3'],
            ['another', 'good', 'sent4'],
            ['another', 'good', 'sent5'],
            ['another', 'good', 'sent6'],
            ['another', 'good', 'sent7'],
            ['another', 'good', 'sent8'],
        ]
    )
    fragments_maker('', doc, max_fragment_length=4, max_chars_cnt=0, min_sent_length=2, overlap=2)

    fragments = doc.get_fragments()
    print(doc)
    assert fragments is not None
    assert len(fragments) == 3
    assert fragments[0] == (0, 3)
    assert fragments[1] == (2, 5)
    assert fragments[2] == (4, 7)
