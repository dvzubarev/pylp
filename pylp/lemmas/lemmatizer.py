#!/usr/bin/env python
# coding: utf-8

import logging
import pylp.common as lp

from pylp.lemmas.ru_lemmatizer import RuLemmatizer
from pylp import lp_doc


class Lemmatizer:
    def __init__(self, *args, **kwargs):
        self._lemmatizers = {lp.Lang.RU: RuLemmatizer(*args, **kwargs)}

    def __call__(self, doc_obj: lp_doc.Doc):
        l = doc_obj.lang
        if l is None:
            logging.warning("Lemmatizer: Lang is not set for document")
            return
        if l in self._lemmatizers:
            self._lemmatizers[l](doc_obj)
