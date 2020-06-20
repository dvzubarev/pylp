#!/usr/bin/env python
# coding: utf-8

import logging
import enum

from ex_pylp.filtratus import Filtratus
from ex_pylp.common import Attr
from ex_pylp.common import PosTag
from ex_pylp.common import SyntLink

class PostProcessor:
    def __init__(self, kinds, **proc_kwargs):
        self._procs = {}
        for k in kinds:
            kwargs = proc_kwargs.get(k, {})
            self._procs[k] = create_postprocessor(k, **kwargs)

    def __call__(self, kinds, text, doc_obj, **proc_params):
        for k in kinds:
            if k not in self._procs:
                raise RuntimeError("PostProcessor %s is not loaded!" % k)

            params_key = k + '_params'
            params = proc_params.get(params_key, {})
            self._procs[k](text, doc_obj, **params)

def create_postprocessor(kind, **kwargs):
    if kind == Filtratus.name:
        return Filtratus(**kwargs)
    if kind == PrepositionCompressor.name:
        return PrepositionCompressor(**kwargs)
    if kind == FragmentsMaker.name:
        return FragmentsMaker(**kwargs)
    raise RuntimeError("Unknown postprocessor: %s" % kind)


class Order(enum.IntEnum):
    BEFORE_FILTRATUS = 0
    AFTER_FILTRATUS = 0

class AbcPostProcessor:
    def __call__(self, text, doc_obj):
        raise NotImplementedError("ABC")

class PrepositionCompressor(AbcPostProcessor):
    name = "preposition_compressor"
    def __init__(self):
        self._prep_whitelist = frozenset([18370182862529888470])

    def __call__(self, text, doc_obj):
        for s in doc_obj['sents']:
            self._proc_sent(s, doc_obj['word_ids'])

    def _proc_sent(self, sent, word_ids):
        for pos, wobj in enumerate(sent):

            if wobj.get(Attr.POS_TAG) == PosTag.ADP and \
               wobj.get(Attr.SYNTAX_LINK_NAME) == SyntLink.CASE:
                head_offs = wobj.get(Attr.SYNTAX_PARENT)
                if not head_offs:
                    continue
                head_pos = pos + head_offs
                head_obj = sent[head_pos]

                head_obj[Attr.PREP_MOD] = wobj[Attr.WORD_NUM]
                if word_ids[wobj[Attr.WORD_NUM]] in self._prep_whitelist:
                    head_obj[Attr.PREP_WHITE_LIST] = True


class FragmentsMaker(AbcPostProcessor):
    name = "fragments_maker"
    def __init__(self):
        pass

    def __call__(self, text, doc_obj, fragment_length = 20, min_sent_length = 4, overlap = 2):
        for sent in doc_obj['sents']:
            pass
