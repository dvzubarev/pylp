#!/usr/bin/env python

import copy

from pylp import lp_doc
import pylp.common as lp
from pylp.phrases.phrase import Phrase
from pylp.word_obj import WordObj
from pylp.phrases.builder import (
    PhraseBuilder,
)
from pylp.phrases.inflect import inflect_phrase
from pylp.phrases.phrase import Phrase
from pylp.common import (
    PosTag,
    WordGender,
    WordCase,
    Lang,
    SyntLink,
)


def _mkw(lemma, link, PoS=lp.PosTag.UNDEF, link_kind=None):
    return WordObj(lemma=lemma, pos_tag=PoS, parent_offs=link, synt_link=link_kind)


def _make_prhases(sent):
    phrase_builder = PhraseBuilder(MaxN=4)
    phrases = phrase_builder.build_phrases_for_sent(sent)
    return phrases


def test_str_repr_after_deser_1():
    words = [
        _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('of', 1, lp.PosTag.ADP, lp.SyntLink.CASE),
        _mkw('h2', -2, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)
    phrases = _make_prhases(sent)

    assert len(phrases) == 1
    phrase = phrases[0]
    assert phrase.get_str_repr() == 'h1 of h2'

    phrase_dict = copy.deepcopy(phrase.to_dict())
    restored_phrase = Phrase.from_dict(phrase_dict)
    assert restored_phrase.get_str_repr() == 'h1 of h2'
    assert restored_phrase.size() == phrase.size()
    assert restored_phrase.get_id() == phrase.get_id()

    phrase_dict2 = copy.deepcopy(phrase.to_dict(use_shorthand_keys=True))
    restored_phrase2 = Phrase.from_dict(phrase_dict2)
    assert restored_phrase2.get_str_repr() == 'h1 of h2'
    assert restored_phrase2.size() == phrase.size()
    assert restored_phrase2.get_id() == phrase.get_id()


def test_str_repr_after_deser_2():
    words = [
        _mkw('h1', 0, lp.PosTag.NOUN, lp.SyntLink.ROOT),
        _mkw('h2', -1, lp.PosTag.NOUN, lp.SyntLink.NMOD),
    ]
    sent = lp_doc.Sent(words)
    phrases = _make_prhases(sent)

    assert len(phrases) == 1
    phrase = phrases[0]
    assert phrase.get_str_repr() == 'h1 h2'

    phrase_dict = copy.deepcopy(phrase.to_dict())
    restored_phrase = Phrase.from_dict(phrase_dict)
    assert restored_phrase.get_str_repr() == 'h1 h2'
    assert restored_phrase.size() == phrase.size()
    assert restored_phrase.get_id() == phrase.get_id()

    phrase_dict2 = copy.deepcopy(phrase.to_dict(use_shorthand_keys=True))
    restored_phrase2 = Phrase.from_dict(phrase_dict2)
    assert restored_phrase2.get_str_repr() == 'h1 h2'
    assert restored_phrase2.size() == phrase.size()


def test_inflect_after_deser_1():
    sent = lp_doc.Sent(
        [
            WordObj(
                lemma='путь',
                pos_tag=PosTag.NOUN,
                gender=WordGender.MASC,
                synt_link=lp.SyntLink.ROOT,
            ),
            WordObj(lemma='к', pos_tag=PosTag.ADP, parent_offs=1, synt_link=lp.SyntLink.CASE),
            WordObj(
                lemma='вершина',
                pos_tag=PosTag.NOUN,
                gender=WordGender.FEM,
                case=WordCase.DAT,
                parent_offs=-2,
                synt_link=SyntLink.NMOD,
            ),
        ]
    )
    phrases = _make_prhases(sent)
    assert len(phrases) == 1
    phrase = phrases[0]

    phrase_dict = copy.deepcopy(phrase.to_dict())
    restored_phrase = Phrase.from_dict(phrase_dict)

    inflect_phrase(restored_phrase, sent, Lang.RU)
    assert restored_phrase.get_words() == ['путь', 'вершине']
    assert restored_phrase.get_str_repr() == 'путь к вершине'
    assert restored_phrase.get_id() == phrase.get_id()

    assert phrase.get_words() == ['путь', 'вершина']
