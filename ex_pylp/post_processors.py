#!/usr/bin/env python
# coding: utf-8

import logging

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
            logging.info("Loading %s postprocessor!", k)

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

    def _sent_chars_cnt(self, doc_obj, sent):
        return sum(len(doc_obj['words'][wobj[Attr.WORD_NUM]]) for wobj in sent)

    def __call__(self, text, doc_obj, max_fragment_length = 20,
                 max_chars_cnt = 5_000, min_sent_length = 4, overlap = 2):
        good_sents = []
        fragments = []
        fragment_size = 0
        fragment_chars_cnt = 0
        fragment_begin_no = 0

        num = -1
        for num, sent in enumerate(doc_obj['sents']):
            if max_chars_cnt:
                fragment_chars_cnt += self._sent_chars_cnt(doc_obj, sent)

            if len(sent) >= min_sent_length:
                fragment_size += 1
                good_sents.append(num)

            if fragment_size >= max_fragment_length or \
               (max_chars_cnt and fragment_chars_cnt > max_chars_cnt):

                fragments.append((fragment_begin_no, num))
                if overlap and good_sents and \
                   good_sents[-min(overlap, len(good_sents))] > fragment_begin_no:
                    fragment_begin_no = good_sents[-min(overlap, len(good_sents))]
                else:
                    fragment_begin_no = num + 1

                fragment_size = overlap
                if max_chars_cnt:
                    fragment_chars_cnt = sum(self._sent_chars_cnt(doc_obj, s)
                                             for s in doc_obj['sents'][fragment_begin_no:num+1])


        if num != -1 and fragment_begin_no < len(doc_obj['sents']):
            fragments.append((fragment_begin_no, len(doc_obj['sents']) - 1))

        logging.debug("created %d fragments", len(fragments))
        doc_obj['fragments'] = fragments
