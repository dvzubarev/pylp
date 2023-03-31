#!/usr/bin/env python
# coding: utf-8

from typing import Any, List
from collections.abc import Iterable
import collections

import logging

from pylp.phrases.builder import (
    BasicPhraseBuilder,
    PhraseBuilder,
    PhraseBuilderOpts,
    MWEBuilderOpts,
)
from pylp.phrases.phrase import Phrase

from pylp import lp_doc
from pylp.word_obj import WordObj


def _add_mwe_to_words(
    sent_words: List[WordObj],
    phrases: Iterable[Phrase],
):

    sorted_phrases = sorted(phrases, key=lambda p: -p.size())
    if not sorted_phrases:
        return

    added_phrases: list[list[Phrase]] = [[] for _ in range(len(sent_words))]
    for p in sorted_phrases:
        for pos in p.get_sent_pos_list():
            if (head_phrases := added_phrases[pos]) and any(hp.contains(p) for hp in head_phrases):
                # phrase is completely overlapped by already added phrase
                break
        else:
            head_word = sent_words[p.sent_hp()]
            head_word.mwes.append(p)
            for pos in p.get_sent_pos_list():
                added_phrases[pos].append(p)


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
    mwe_opts=None,
):

    if mwe_opts is None:
        mwe_opts = MWEBuilderOpts()
    if not mwe_opts.mwe_size:
        mwe_size = MaxN
    else:
        mwe_size = mwe_opts.mwe_size
    mwe_builder: BasicPhraseBuilder = builder_cls(mwe_size, mwe_opts)
    for sent in doc_obj:
        phrases = mwe_builder.build_phrases_for_sent(sent)
        _add_mwe_to_words(list(sent.words()), phrases)

    if builder_opts is None:
        builder_opts = PhraseBuilderOpts()

    builder: BasicPhraseBuilder = builder_cls(MaxN, builder_opts)

    for sent in doc_obj:
        phrases = builder.build_phrases_for_sent(sent)
        sent.set_phrases(phrases)
    if min_cnt:
        remove_rare_phrases(doc_obj, min_cnt=min_cnt)


def replace_words_with_phrases(
    sent_words: List[Any],
    phrases: Iterable[Phrase],
    allow_overlapping_phrases=True,
    sort_key=lambda p: -p.size(),
    keep_filler=False,
    filler=None,
) -> List[Any | Phrase]:
    """phrases are list of prhases from the build_phrases_iter function"""

    def testp(w):
        return isinstance(w, Phrase) or w == filler

    sorted_phrases = sorted(phrases, key=sort_key)
    if not sorted_phrases:
        return sent_words

    new_sent: List[Any] = list(range(len(sent_words)))
    logging.debug("new sent: %s", new_sent)
    pred = all if allow_overlapping_phrases else any
    for p in sorted_phrases:
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
