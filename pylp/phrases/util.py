#!/usr/bin/env python
# coding: utf-8

from typing import Any, Iterator, List
import collections
import logging

from pylp.phrases.builder import BasicPhraseBuilder, PhraseBuilder, PhraseBuilderOpts, Phrase
from pylp.phrases.phrase import Phrase

from pylp import lp_doc


def remove_rare_phrases(doc_obj: lp_doc.Doc, min_cnt=1):
    if min_cnt <= 0:
        return

    counter = collections.Counter()
    for sent in doc_obj:
        for p in sent.phrases():
            counter[p.get_id()] += 1
    for sent in doc_obj:
        new_phrases = []
        for p in sent.phrases():
            if counter[p.get_id()] >= min_cnt:
                new_phrases.append(p)
        sent.set_phrases(new_phrases)


def add_phrases_to_doc(
    doc_obj: lp_doc.Doc,
    MaxN,
    min_cnt=0,
    builder_cls=PhraseBuilder,
    builder_opts=None,
):
    if builder_opts is None:
        builder_opts = PhraseBuilderOpts()

    builder: BasicPhraseBuilder = builder_cls(MaxN, builder_opts)
    builder.build_phrases_for_doc(doc_obj)
    if min_cnt:
        remove_rare_phrases(doc_obj, min_cnt=min_cnt)


def make_phrases(
    sent: lp_doc.Sent,
    MaxN,
    builder_cls=PhraseBuilder,
    builder_opts=PhraseBuilderOpts(),
):
    builder: BasicPhraseBuilder = builder_cls(MaxN, builder_opts)
    phrases = builder.build_phrases_for_sent(sent)
    return phrases


def replace_words_with_phrases(
    sent_words: List[Any],
    phrases: Iterator[Phrase],
    allow_overlapping_phrases=True,
    sort_key=lambda p: -p.size(),
    keep_filler=False,
    filler=None,
) -> List[Any | Phrase]:
    """phrases are list of prhases from the build_phrases_iter function"""

    if not phrases:
        return sent_words

    def testp(w):
        return isinstance(w, Phrase) or w == filler

    phrases.sort(key=sort_key)

    new_sent: List[Any] = list(range(len(sent_words)))
    logging.debug("new sent: %s", new_sent)
    pred = all if allow_overlapping_phrases else any
    for p in phrases:
        if pred(testp(new_sent[pos]) for pos in p.get_sent_pos_list()):
            # overlapping with other phrase
            continue
        added = False
        for pos in p.get_sent_pos_list():
            if not testp(new_sent[pos]):
                if not added:
                    new_sent[pos] = p
                    added = True
                else:
                    new_sent[pos] = filler

    logging.debug("sent with phrases: %s", new_sent)
    if not keep_filler:
        return [w if isinstance(w, Phrase) else sent_words[w] for w in new_sent if w != filler]

    return [w if testp(w) else sent_words[w] for w in new_sent]
