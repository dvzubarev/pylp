#!/usr/bin/env python
# coding: utf-8

import collections
import logging
from pylp.phrases.builder import PhraseBuilder, PhraseBuilderOpts, Phrase


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
    min_cnt=0,
    builder_cls=PhraseBuilder,
    builder_opts=PhraseBuilderOpts(),
):
    builder = builder_cls(MaxN, builder_opts)
    word_ids = doc_obj.get('word_ids')
    words = None
    if use_words:
        words = doc_obj['words']

    phrases = builder.build_phrases_for_sents(doc_obj['sents'], words, word_ids=word_ids)
    if min_cnt:
        phrases = remove_rare_phrases(phrases, min_cnt=min_cnt)
    doc_obj['sent_phrases'] = phrases


def make_phrases(
    sent,
    words,
    MaxN,
    builder_cls=PhraseBuilder,
    builder_opts=PhraseBuilderOpts(),
):
    builder = builder_cls(MaxN, builder_opts)
    phrases = builder.build_phrases_for_sent(sent, words)
    return phrases


def replace_words_with_phrases(
    sent_words,
    phrases,
    allow_overlapping_phrases=True,
    sort_key=lambda p: -p.size(),
    keep_filler=False,
    filler=None,
):
    """phrases are list of prhases from the build_phrases_iter function"""

    if not phrases:
        return sent_words

    def testp(w):
        return isinstance(w, Phrase) or w == filler

    phrases.sort(key=sort_key)

    new_sent = list(range(len(sent_words)))
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
