#!/usr/bin/env python
# coding: utf-8

from pylp.common import Attr

import libpyexbase


def word_id_combiner(words):
    w = words[0]
    for i in range(1, len(words)):
        w = libpyexbase.combine_word_id(w, words[i])
    return w


def make_words_dict(doc):
    # TODO Sort words by freq
    # most frequent words should have smaller indexes
    d = {}
    flatten_words = []
    for sent in doc:
        for w in sent:
            if w not in d:
                d[w] = len(flatten_words)
                flatten_words.append(w)

    return flatten_words, d


def adjust_syntax_links(new_sent, old_sent, new_positions):
    """Example:
    old_sent: ['word', ',', 'word2', ':', 'word3']
    new_sent: ['word', 'word2', 'word3']
    new_positions: [0, -1, 1, -1, 2]

    word links with word2
    word2 links with word3
    """
    for old_pos, old_word in enumerate(old_sent):
        if new_positions[old_pos] == -1:
            # this word does not exist anymore
            continue
        new_pos = new_positions[old_pos]

        old_parent_offs = new_sent[new_pos].get(Attr.SYNTAX_PARENT)
        if old_parent_offs is None:
            # this is root or no link
            continue
        old_parent_pos = old_pos + old_parent_offs

        new_parent_pos = new_positions[old_parent_pos]
        if new_parent_pos == -1:
            # parent does not exist
            if Attr.SYNTAX_LINK_NAME in new_sent[new_pos]:
                del new_sent[new_pos][Attr.SYNTAX_LINK_NAME]
            if Attr.SYNTAX_PARENT in new_sent[new_pos]:
                del new_sent[new_pos][Attr.SYNTAX_PARENT]

        else:
            new_sent[new_pos][Attr.SYNTAX_PARENT] = new_parent_pos - new_pos
