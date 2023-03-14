#!/usr/bin/env python
# coding: utf-8

import collections
from typing import List, Mapping, Tuple
import pickle
import gzip
import os
import logging

import libpyexbase

import pylp.common as lp

from pylp.lemmas.abc_lemmatizer import AbcLemmatizer
from pylp.lemmas.ru_lemmatizer import RuLemmatizer
from pylp.lemmas.en_lemmatizer import EnLemmatizer
from pylp import lp_doc
from pylp.word_obj import WordObj


def _find_dict_path(explicit_path=''):
    if explicit_path:
        return explicit_path

    res_dir = os.environ.get('PYLP_RESOURCES_DIR')
    if res_dir is None:
        raise RuntimeError("Env var PYLP_RESOURCES_DIR is not set!")

    name = os.environ.get('PYLP_LEMMAS_DICT_NAME', 'lemma.ruen.v1.pickle.gz')
    path = res_dir + '/' + name
    if not os.path.exists(path):
        raise RuntimeError(f"Lemmas dict ({path}) does not exist")
    return path


ImpFeatsType = Tuple[int | None, int | None, int | None, int | None]
LemmasDictType = Mapping[Tuple[str, int], List[Tuple[ImpFeatsType, str, int]]]


class Lemmatizer(AbcLemmatizer):
    """General dict-based lemmatizier"""

    def __init__(self, *args, **kwargs):
        dicts_path = _find_dict_path()
        with gzip.open(dicts_path, 'rb') as inpf:

            self._lemmas_dict: LemmasDictType = pickle.load(inpf)
        self._lang_lemmatizers: Mapping[lp.Lang, AbcLemmatizer] = {
            lp.Lang.RU: RuLemmatizer(*args, **kwargs),
            lp.Lang.EN: EnLemmatizer(*args, **kwargs),
        }

        self._min_occ_cnt = 3

    def _should_early_dispatch(self, word_obj: lp_doc.WordObj) -> lp.Lang | None:
        if word_obj.pos_tag in (lp.PosTag.PARTICIPLE_SHORT, lp.PosTag.PARTICIPLE):
            word_lang = libpyexbase.lang_of_word(word_obj.form)
            if word_lang == lp.Lang.RU:
                return word_lang

        return None

    def _find_dict_lemmas(self, form: str, word_obj: lp_doc.WordObj):
        token_str = form.lower()
        pos_tag = word_obj.pos_tag
        variants = self._lemmas_dict.get((token_str, pos_tag))
        logging.debug(
            "form=%s; pos_tag=%s; vars=%s; variants=%s",
            form,
            pos_tag,
            len(variants) if variants is not None else 0,
            variants,
        )
        if variants is None:
            return []

        best_variants = collections.defaultdict(int)
        cur_best_score = 0
        # IMPORTANT_FEATS = ['Case', 'Gender', 'Number', 'Tense']
        for feats, lemma, cnt in variants:
            if lemma == '':
                lemma = token_str
            var_score = 0
            if feats and word_obj.case is not None and word_obj.case == feats[0]:
                var_score += 1
            if feats and word_obj.gender is not None and word_obj.gender == feats[1]:
                var_score += 1
            if feats and word_obj.number is not None and word_obj.number == feats[2]:
                var_score += 1
            if feats and word_obj.tense is not None and word_obj.tense == feats[3]:
                var_score += 1

            if var_score > cur_best_score:
                best_variants.clear()
                best_variants[lemma] += cnt
                cur_best_score = var_score
            elif var_score == cur_best_score:
                best_variants[lemma] += cnt

        best_variants = list(best_variants.items())
        logging.debug(
            "form=%s; pos_tag=%s; vars=%s; best_variants=%s",
            form,
            pos_tag,
            len(best_variants),
            best_variants,
        )
        return best_variants

    def _dispatch_to_lang_lemmatizier(
        self,
        word_obj: lp_doc.WordObj,
        variants: List[Tuple[str, int]] | None = None,
        word_lang: lp.Lang | None = None,
    ) -> str | None:
        if word_lang is None:
            word_lang = libpyexbase.lang_of_word(word_obj.form)
            assert word_lang is not None, "Logic error 484249"

        if word_lang == lp.Lang.UNDEF:
            return word_obj.form

        lemmatizer = self._lang_lemmatizers.get(word_lang)
        if lemmatizer is None:
            logging.warning("Lemmatizer: Lang %s is not supported", word_lang)
            return word_obj.form
        lemma = lemmatizer.produce_lemma(word_obj, variants)
        if lemma is not None:
            return lemma
        if variants is not None:
            # select from dict_variants the most frequent one
            most_frequent = max(variants, key=lambda t: -t[1])
            return most_frequent[0]
        return None

    def _finalize_lemma(self, lemma, word_obj: WordObj):
        if word_obj.pos_tag == lp.PosTag.PROPN:
            assert word_obj.form is not None, "Logic error 1333"
            if word_obj.form.isupper():
                return lemma.upper()
            return lemma.title()
        return lemma

    def _produce_lemma_impl(self, word_obj: WordObj, _=None) -> str | None:
        if word_obj.form is None:
            return None

        if (dispatch_lang := self._should_early_dispatch(word_obj)) is not None:
            return self._dispatch_to_lang_lemmatizier(word_obj, word_lang=dispatch_lang)
        best_variants = self._find_dict_lemmas(word_obj.form, word_obj)
        if not best_variants:
            return self._dispatch_to_lang_lemmatizier(word_obj)

        if len(best_variants) == 1 and best_variants[0][1] > self._min_occ_cnt:
            return best_variants[0][0]

        return self._dispatch_to_lang_lemmatizier(word_obj, best_variants)

    def produce_lemma(
        self, word_obj: WordObj, lemmas_freq_list: List[Tuple[str, int]] | None = None
    ) -> str | None:
        lemma = self._produce_lemma_impl(word_obj, lemmas_freq_list)
        if lemma is not None:
            return self._finalize_lemma(lemma, word_obj)
        return None

    def __call__(self, doc_obj: lp_doc.Doc):
        for sent in doc_obj:
            for word_obj in sent:
                if not word_obj.form:
                    logging.warning("Lemmatizer: Empty form in the word %s", word_obj)
                    continue
                lemma = self.produce_lemma(word_obj)
                if lemma:
                    word_obj.lemma = lemma
