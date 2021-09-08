#!/usr/bin/env python
# coding: utf-8

import collections
import logging
from pylp.utils import word_id_combiner
from pylp.phrases.builder import PhraseBuilder, PhraseBuilderOpts


def remove_rare_phrases(sent_phrases, min_cnt=1):
    if min_cnt <= 0:
        return sent_phrases

    counter = collections.Counter()
    for sent in sent_phrases:
        for p in sent:
            counter[p.get_id()] += 1
    new_sents = []
    for sent in sent_phrases:
        new_sent = []
        for p in sent:
            if counter[p.get_id()] >= min_cnt:
                new_sent.append(p)

        new_sents.append(new_sent)

    return new_sents


def add_phrases_to_doc(
    doc_obj,
    MaxN,
    use_words=False,
    combiner=word_id_combiner,
    min_cnt=0,
    builder_cls=PhraseBuilder,
    builder_opts=PhraseBuilderOpts(),
):
    builder = builder_cls(MaxN, combiner, builder_opts)
    text_obj = doc_obj['text']
    words = text_obj['words'] if use_words else text_obj['word_ids']
    phrases = builder.build_phrases_for_sents(text_obj['sents'], words)
    if min_cnt:
        phrases = remove_rare_phrases(phrases, min_cnt=min_cnt)
    text_obj['sent_phrases'] = phrases


def make_phrases(
    sent,
    words,
    MaxN,
    combiner=word_id_combiner,
    builder_cls=PhraseBuilder,
    builder_opts=PhraseBuilderOpts(),
):
    builder = builder_cls(MaxN, combiner, builder_opts)
    phrases = builder.build_phrases_for_sent(sent, words)
    return phrases


def replace_words_with_phrases(sent_words, phrases, allow_overlapping_phrases=True):
    """phrases are list of prhases from the build_phrases_iter function"""

    if not phrases:
        return sent_words

    phrases.sort(key=lambda p: -p.size())

    new_sent = list(range(len(sent_words)))
    logging.debug("new sent: %s", new_sent)
    pred = all if allow_overlapping_phrases else any
    for p in phrases:
        if pred(isinstance(new_sent[pos], tuple) for pos in p.get_sent_pos_list()):
            # overlapping with other phrase
            continue
        added = False
        for pos in p.get_sent_pos_list():
            if not isinstance(new_sent[pos], tuple):
                if not added:
                    new_sent[pos] = (p,)
                    added = True
                else:
                    new_sent[pos] = tuple()

    logging.debug("sent with phrases: %s", new_sent)
    return [w[0] if isinstance(w, tuple) else sent_words[w] for w in new_sent if w != ()]
