#!/usr/bin/env python
# coding: utf-8

import logging

from ex_pylp.common import Attr
from ex_pylp.common import PosTag
from ex_pylp.common import SyntLink

class PostProcessor:
    def __init__(self, kinds):
        self._procs = {}
        for k in kinds:
            self._procs[k] = create_postprocessor(k)

    def __call__(self, kinds, doc_obj):
        for k in kinds:
            if k not in self._procs:
                raise RuntimeError("PostProcessor %s is not loaded!" % k)

            self._procs[k](doc_obj)

def create_postprocessor(kind):
    if kind == PrepositionCompressor.name:
        return PrepositionCompressor()
    raise RuntimeError("Unknown postprocessor: %s" % kind)


class AbcPostProcessor:
    def __call__(self, doc_obj):
        raise NotImplementedError("ABC")

class PrepositionCompressor(AbcPostProcessor):
    name = "preposition_compressor"
    def __init__(self):
        self._prep_whitelist = frozenset([18370182862529888470])

    def __call__(self, doc_obj):
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
                #TEMP
                if Attr.PREP_MOD in head_obj:
                    logging.warning("Unexpected situation!")

                head_obj[Attr.PREP_MOD] = wobj[Attr.WORD_NUM]
                if word_ids[wobj[Attr.WORD_NUM]] in self._prep_whitelist:
                    head_obj[Attr.PREP_WHITE_LIST] = True
