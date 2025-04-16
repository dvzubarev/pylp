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
    PhraseBuilderProfileArgs,
    dispatch_phrase_building,
)
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
    phrases_max_n: int,
    min_cnt: int = 0,
    profile_name: str = '',
    profile_args: PhraseBuilderProfileArgs = PhraseBuilderProfileArgs(),
    builder_opts=None,
    builder_cls=PhraseBuilder,
):
    """Pass either profile_name or builder_opts. If profile_name is not empty
    call dispatch_phrase_building with specified profile_name. Otherwise call
    builder_cls(phrases_max_n, builder_opts).build_phrases_for_sent for each
    sentence in the doc.
    """
    if not profile_name and builder_opts is None:
        raise RuntimeError("Pass either profile_name or builder_opts!")
    if profile_name and builder_opts:
        raise RuntimeError("Pass either profile_name or builder_opts!")

    if profile_name:
        for sent in doc_obj:
            phrases = dispatch_phrase_building(
                profile_name,
                sent,
                phrases_max_n,
                profile_args=profile_args,
                builder_cls=builder_cls,
            )
            sent.set_phrases(phrases)
    else:
        builder_opts = PhraseBuilderOpts()
        builder: BasicPhraseBuilder = builder_cls(phrases_max_n, builder_opts)
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
