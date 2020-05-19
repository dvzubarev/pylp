#!/usr/bin/env python
# coding: utf-8



def make_words_dict(doc):
    #TODO Sort words by freq
    #most frequent words should have smaller indexes
    d = {}
    flatten_words = []
    for sent in doc:
        for w in sent:
            if w not in d:
                d[w] = len(flatten_words)
                flatten_words.append(w)

    return flatten_words, d
