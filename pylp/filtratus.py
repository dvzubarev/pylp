#!/usr/bin/env python
# coding: utf-8


import logging

from pylp.common import PosTag
from pylp.common import Lang
from pylp.common import STOP_WORD_POS_TAGS

from pylp import lp_doc
from pylp.word_obj import WordObj


class Filtratus:
    name = "filtratus"

    def __init__(self, kinds, filters_kwargs):
        self._filters = {}
        for k in kinds:
            self._filters[k] = create_filtratus(k, **filters_kwargs)

    def __call__(self, text: str, doc_obj: lp_doc.Doc, kinds):
        filters = []
        for k in kinds:
            if k not in self._filters:
                raise RuntimeError("Filter %s is not loaded!" % k)
            filters.append(self._filters[k])

        for sent in doc_obj:
            sent.filter_words(filters)


class AbcFilter:
    def __init__(self, **kwargs):
        pass

    def filter(self, word_obj: WordObj, word_pos: int, sent: lp_doc.Sent):
        raise NotImplementedError("ABC")

    def __call__(self, word_obj: WordObj, word_pos: int, sent: lp_doc.Sent) -> bool:
        return self.filter(word_obj, word_pos, sent)


class PunctAndUndefFiltratus(AbcFilter):
    name = 'punct'

    def filter(self, word_obj: WordObj, word_pos: int, sent: lp_doc.Sent):
        return word_obj.pos_tag in (PosTag.UNDEF, PosTag.PUNCT, PosTag.X)


class DeterminatusFiltratus(AbcFilter):
    name = 'determiner'

    def filter(self, word_obj: WordObj, word_pos: int, sent: lp_doc.Sent):
        return word_obj.pos_tag == PosTag.DET


class CommonAuxFiltratus(AbcFilter):
    name = 'common_aux'

    def __init__(self, **kwargs):
        self._common_aux = frozenset(['be', 'have'])

    def filter(self, word_obj: WordObj, word_pos: int, sent: lp_doc.Sent):

        return word_obj.pos_tag == PosTag.AUX and word_obj.lemma in self._common_aux


class StopWordsFiltratus(AbcFilter):
    name = 'stopwords'

    def __init__(self, sw_pos_tags=None, sw_list_path='', sw_white_list_path='', **kwargs):
        def load_words_list(p):
            if p:
                with open(p, 'r', encoding='utf8') as f:
                    return frozenset(l.strip() for l in f)
            else:
                return []

        super().__init__(**kwargs)

        self._stop_words = load_words_list(sw_list_path)
        logging.info("Loaded %d stopwords", len(self._stop_words))
        self._white_list = load_words_list(sw_white_list_path)
        logging.info("Loaded %d words from white list", len(self._white_list))

        if sw_pos_tags is None:
            self._sw_pos_tags = frozenset(STOP_WORD_POS_TAGS)
        else:
            self._sw_pos_tags = frozenset(sw_pos_tags)

    def filter(self, word_obj: WordObj, word_pos: int, sent: lp_doc.Sent):

        if self._white_list and word_obj.lemma in self._white_list:
            return False

        if word_obj.pos_tag in self._sw_pos_tags:
            return True

        if self._stop_words and word_obj.lemma in self._stop_words:
            return True

        return False


class NumAndUndefLangFiltratus(AbcFilter):
    name = 'num&undeflang'

    def filter(self, word_obj: WordObj, word_pos: int, sent: lp_doc.Sent):
        return word_obj.lang == Lang.UNDEF or word_obj.pos_tag == PosTag.NUM


def create_filtratus(kind='', **kwargs):
    if kind == PunctAndUndefFiltratus.name:
        return PunctAndUndefFiltratus(**kwargs)
    if kind == DeterminatusFiltratus.name:
        return DeterminatusFiltratus(**kwargs)
    if kind == CommonAuxFiltratus.name:
        return CommonAuxFiltratus(**kwargs)
    if kind == StopWordsFiltratus.name:
        return StopWordsFiltratus(**kwargs)
    if kind == NumAndUndefLangFiltratus.name:
        return NumAndUndefLangFiltratus(**kwargs)

    raise RuntimeError("Unknown filtratus kind: %s" % kind)
