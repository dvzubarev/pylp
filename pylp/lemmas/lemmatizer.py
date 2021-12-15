#!/usr/bin/env python
# coding: utf-8

import pylp.common as lp

from pylp.lemmas.ru_lemmatizer import RuLemmatizer


class Lemmatizer:
    def __init__(self, *args, **kwargs):
        self._lemmatizers = {lp.Lang.RU: RuLemmatizer(*args, **kwargs)}

    def __call__(self, doc_obj):
        l = doc_obj['lang']
        if l in self._lemmatizers:
            self._lemmatizers[l](doc_obj)
            return
