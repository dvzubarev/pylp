#!/usr/bin/env python
# coding: utf-8


import logging


from pylp.filtratus import Filtratus
from pylp.common import Attr
from pylp.common import PosTag
from pylp.common import SyntLink
from pylp.common import PREP_WHITELIST

from pylp import lp_doc


class PostProcessor:
    def __init__(self, kinds, **proc_kwargs):
        self._procs = {}
        for k in kinds:
            kwargs = proc_kwargs.get(k, {})
            self._procs[k] = create_postprocessor(k, **kwargs)
            logging.info("Loading %s postprocessor!", k)

    def __call__(self, kinds, text: str, doc_obj: lp_doc.Doc, **proc_params):
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

    def __init__(self, **kwargs):
        pass

    def __call__(self, text, doc_obj):
        raise RuntimeError("Logic error; this code does not work with new pylp version")
        # TODO this code works with old version of pylp
        # PrepositionCompressor is not used in recent versions since we don't filter prepositions
        # but this idea  may be used later for reducing space by deleting some aux words and
        # moving their essentials to the head word
        for s in doc_obj['sents']:
            self._proc_sent(s, doc_obj['word_ids'])

    def _proc_sent(self, sent, word_ids):
        for pos, wobj in enumerate(sent):

            if (
                wobj.get(Attr.POS_TAG) == PosTag.ADP
                and wobj.get(Attr.SYNTAX_LINK_NAME) == SyntLink.CASE
            ):
                parent_offs = wobj.get(Attr.SYNTAX_PARENT)
                if not parent_offs:
                    continue
                parent_pos = pos + parent_offs
                head_obj = sent[head_pos]

                head_obj[Attr.PREP_MOD] = wobj[Attr.WORD_NUM]
                if word_ids[wobj[Attr.WORD_NUM]] in PREP_WHITELIST:
                    head_obj[Attr.PREP_WHITE_LIST] = True


class FragmentsMaker(AbcPostProcessor):
    name = "fragments_maker"

    def __init__(self):
        pass

    def _chars_cnt(self, sent: lp_doc.Sent):
        return sum(len(wobj.lemma) for wobj in sent)

    def __call__(
        self,
        text: str,
        doc_obj: lp_doc.Doc,
        max_fragment_length=20,
        max_chars_cnt=5_000,
        min_sent_length=4,
        overlap=2,
    ):
        good_sents = []
        fragments = []
        fragment_size = 0
        fragment_chars_cnt = 0
        fragment_begin_no = 0

        num = -1
        for num, sent in enumerate(doc_obj):
            if max_chars_cnt:
                # TODO calculate chars cnt based on text?
                fragment_chars_cnt += self._chars_cnt(sent)

            if len(sent) >= min_sent_length:
                fragment_size += 1
                good_sents.append(num)

            if fragment_size >= max_fragment_length or (
                max_chars_cnt and fragment_chars_cnt > max_chars_cnt
            ):

                fragments.append((fragment_begin_no, num))
                if (
                    overlap
                    and good_sents
                    and good_sents[-min(overlap, len(good_sents))] > fragment_begin_no
                ):
                    fragment_begin_no = good_sents[-min(overlap, len(good_sents))]
                else:
                    fragment_begin_no = num + 1

                fragment_size = overlap
                if max_chars_cnt:
                    fragment_chars_cnt = sum(
                        self._chars_cnt(sent) for sent in doc_obj[fragment_begin_no : num + 1]
                    )

        end = len(doc_obj) - 1
        cur_end = fragments[-1][1] if fragments else -1
        if num != -1 and fragment_begin_no <= end and cur_end != end:
            fragments.append((fragment_begin_no, end))

        logging.debug("created %d fragments", len(fragments))

        doc_obj.set_fragments(fragments)
