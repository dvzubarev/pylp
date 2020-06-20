#!/usr/bin/env python
# coding: utf-8

import logging

from ex_pylp.common import Attr
from ex_pylp.common import PosTag
from ex_pylp.common import Lang
from ex_pylp.common import SyntLink

class FiltratusContext:
    def __init__(self, doc):
        self.word_strings = doc['words']
        self.word_ids = doc['word_ids']
        self.doc_lang = doc['lang']

class Filtratus:
    name = "filtratus"

    def __init__(self, kinds, filters_kwargs):
        self._filters = {}
        for k in kinds:
            kwargs = {}
            if k in filters_kwargs:
                kwargs = filters_kwargs[k]
            self._filters[k] = create_filtratus(k, **kwargs)

    def _adjust_syntax_links(self, new_sent, old_sent, new_positions):
        """Example:
        old_sent: ['word', ',', 'word2', ':', 'word3']
        new_sent: ['word', 'word2', 'word3']
        new_positions: [0, -1, 1, -1, 2]

        word links with word2
        word2 links with word3
        """
        for old_pos, old_word in enumerate(old_sent):
            if new_positions[old_pos] == -1:
                #this word does not exist anymore
                continue
            new_pos = new_positions[old_pos]

            old_parent_offs = new_sent[new_pos].get(Attr.SYNTAX_PARENT)
            if old_parent_offs is None:
                #this is root or no link
                continue
            old_parent_pos = old_pos + old_parent_offs

            new_parent_pos = new_positions[old_parent_pos]
            if new_parent_pos == -1:
                #parent does not exist
                if Attr.SYNTAX_LINK_NAME in new_sent[new_pos]:
                    del new_sent[new_pos][Attr.SYNTAX_LINK_NAME]
                if Attr.SYNTAX_PARENT in new_sent[new_pos]:
                    del new_sent[new_pos][Attr.SYNTAX_PARENT]

            else:
                new_sent[new_pos][Attr.SYNTAX_PARENT] = new_parent_pos - new_pos





    def __call__(self, text, doc_obj, kinds):
        new_sents = []
        ctx = FiltratusContext(doc_obj)
        for sent in doc_obj['sents']:
            new_sent = []
            new_positions = []
            cur_pos = 0
            for word_pos, word_obj in enumerate(sent):
                filtered = False
                for k in kinds:
                    if k not in self._filters:
                        raise RuntimeError("Filter %s is not loaded!" % k)

                    filtered = self._filters[k].filter(word_obj, word_pos, sent, ctx)
                    if filtered:
                        break

                if filtered:
                    new_positions.append(-1)
                else:
                    new_sent.append(word_obj)
                    new_positions.append(cur_pos)
                    cur_pos += 1
            if len(new_sent) != len(sent):
                self._adjust_syntax_links(new_sent, sent, new_positions)
            new_sents.append(new_sent)
        doc_obj['sents'] = new_sents
        #TODO remove unused words from doc_obj['words']


class AbcFilter:
    def filter(self, word_obj, word_pos, sent, ctx):
        raise NotImplementedError("ABC")

class PunctAndUndefFiltratus(AbcFilter):
    name = 'punct'
    def filter(self, word_obj, word_pos, sent, ctx):
        if word_obj.get(Attr.POS_TAG, PosTag.UNDEF) in (PosTag.UNDEF, PosTag.PUNCT) and \
           word_obj.get(Attr.SYNTAX_LINK_NAME, SyntLink.PUNCT) == SyntLink.PUNCT:
            return True
        return False

class DeterminatusFiltratus(AbcFilter):
    name = 'determiner'
    def filter(self, word_obj, word_pos, sent, ctx):
        if word_obj[Attr.POS_TAG] == PosTag.DET:
            return True
        return False

class StopWordsFiltratus(AbcFilter):
    name = 'stopwords'
    def __init__(self, stop_words_list_path = ''):
        if stop_words_list_path:
            with open(stop_words_list_path, 'r') as f:
                self._stop_words = frozenset(int(l.strip(), 16) for l in f)
                logging.info("Loaded %d stopwords", len(self._stop_words))
        else:
            self._stop_words = []

        self._sw_POSes = frozenset([PosTag.ADP, PosTag.CONJ, PosTag.PART, PosTag.PRON,
                                    PosTag.AUX, PosTag.SCONJ, PosTag.CCONJ, PosTag.SYM])


    def filter(self, word_obj, word_pos, sent, ctx):
        if word_obj.get(Attr.STOP_WORD_TYPE, 0) > 0:
            return True

        if word_obj[Attr.POS_TAG] in self._sw_POSes:
            return True

        if self._stop_words and \
           ctx.word_ids[word_obj[Attr.WORD_NUM]] in self._stop_words:
            return True


        return False

class NumAndUndefLangFiltratus(AbcFilter):
    name = 'num&undeflang'
    def filter(self, word_obj, word_pos, sent, ctx):
        word_lang = word_obj.get(Attr.LANG, ctx.doc_lang)
        if word_lang == Lang.UNDEF:
            return True

        #Do not use aot by now
        # PosTag.NUM  - имя числительное,   PosTag.NUMBER - число
        # if word_lang == Lang.RU:
        #     if word_obj[Attr.POS_TAG] == PosTag.NUMBER:
        #         return True
        # else:
        #but by UD PosTag.NUM is any number? and PosTag.NUMBER is not used
        if word_obj[Attr.POS_TAG] == PosTag.NUM:
            return True

        return False


def create_filtratus(kind = '', **kwargs):
    if kind == PunctAndUndefFiltratus.name:
        return PunctAndUndefFiltratus(**kwargs)
    if kind == DeterminatusFiltratus.name:
        return DeterminatusFiltratus(**kwargs)
    if kind == StopWordsFiltratus.name:
        return StopWordsFiltratus(**kwargs)
    if kind == NumAndUndefLangFiltratus.name:
        return NumAndUndefLangFiltratus(**kwargs)

    raise RuntimeError("Unknown filtratus kind: %s" % kind)
