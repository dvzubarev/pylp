#!/usr/bin/env python
# coding: utf-8

import logging
from typing import List, Tuple

import pymorphy2

from pylp import common
from pylp import lp_doc
from pylp.lemmas.abc_lemmatizer import AbcLemmatizer
from pylp.word_obj import WordObj
from pylp.common import PosTag, WordGender, WordCase


class Stat:
    def __init__(self):
        self.fixed_genders = 0
        self.fixed_plural = 0
        self.not_found = 0

    def __str__(self):
        return (
            f"fixed_genders: {self.fixed_genders}, "
            f"fixed plural: {self.fixed_plural}, not found: {self.not_found}"
        )


class RuLemmatizerOpts:
    def __init__(self, fix_feats=False):
        self.fix_feats = fix_feats


_POS_MAPPING = {
    PosTag.ADJ: 'ADJF',
    PosTag.ADJ_SHORT: 'ADJS',
    PosTag.ADV: 'ADVB',
    PosTag.ADP: 'PREP',
    PosTag.DET: 'ADJF',
    PosTag.SCONJ: 'CONJ',
    PosTag.CCONJ: 'CONJ',
    PosTag.INTJ: 'INTJ',
    PosTag.NOUN: 'NOUN',
    PosTag.NUM: 'NUMR',
    PosTag.VERB: 'VERB',
    PosTag.PARTICIPLE: 'PRTF',
    PosTag.PARTICIPLE_SHORT: 'PRTS',
    PosTag.PARTICIPLE_ADVERB: 'GRND',
    PosTag.PROPN: 'NOUN',
    PosTag.PRON: 'NPRO',
    PosTag.PART: 'PRCL',
}


_CASE_MAPPING = {
    'ablt': WordCase.INS,
    'accs': WordCase.ACC,
    'datv': WordCase.DAT,
    'gen1': WordCase.GEN,
    'gen2': WordCase.GEN,
    'gent': WordCase.GEN,
    'loc2': WordCase.LOC,
    'loct': WordCase.LOC,
    'nomn': WordCase.NOM,
    'voct': WordCase.NOM,
}

_GENDER_MAPPING = {
    'femn': WordGender.FEM,
    'masc': WordGender.MASC,
    'neut': WordGender.NEUT,
}

_TENSE_MAPPING = {
    'futr': common.WordTense.FUT,
    'past': common.WordTense.PAST,
    'pres': common.WordTense.PRES,
}


class RuLemmatizer(AbcLemmatizer):
    def __init__(self, opts=RuLemmatizerOpts(), **_):
        self._opts = opts

        self._morph = None
        self._parsed_cache = {}
        self._max_cache_size = 5000

    def _get_pymorphy(self):
        if self._morph is None:
            self._morph = pymorphy2.MorphAnalyzer()
        return self._morph

    def _find_matching_res(self, morphy_tag, results, word_obj: WordObj):
        best_variants = []
        cur_best_score = 0
        for res in results:
            res_pos_tag = res.tag.POS
            if res_pos_tag == 'INFN':
                res_pos_tag = 'VERB'

            if res_pos_tag != morphy_tag:
                continue
            score = 0
            if (
                word_obj.gender is not None
                and res.tag.gender
                and word_obj.gender == _GENDER_MAPPING.get(res.tag.gender)
            ):
                score += 1
            if word_obj.number is not None and res.tag.number:
                morphy_value = 'plur' if word_obj.number == common.WordNumber.PLUR else 'sing'
                if morphy_value == res.tag.number:
                    score += 1
            if (
                word_obj.case is not None
                and res.tag.case
                and _CASE_MAPPING.get(res.tag.case) == word_obj.case
            ):
                score += 1
            if (
                word_obj.tense is not None
                and res.tag.tense
                and _TENSE_MAPPING.get(res.tag.tense) == word_obj.tense
            ):
                score += 1

            if score > cur_best_score:
                best_variants = [res]
                cur_best_score = score
            elif score == cur_best_score:
                best_variants.append(res)

        return best_variants

    def _get_lemma(self, pymorphy_res, morphy_tag) -> str:
        if morphy_tag in ('PRTF', 'PRTS'):
            r = pymorphy_res.inflect({'sing', 'masc', 'nomn'})
            if r is not None:
                return r.word
        return pymorphy_res.normal_form

    def _parse_word(self, word):
        if word not in self._parsed_cache:
            if len(self._parsed_cache) > self._max_cache_size:
                self._parsed_cache.clear()
            self._parsed_cache[word] = self._get_pymorphy().parse(word)
        return self._parsed_cache[word]

    def _get_morphy_tag(self, word_obj: WordObj):
        if word_obj.degree == common.WordDegree.CMP:
            return 'COMP'

        return _POS_MAPPING.get(word_obj.pos_tag)

    def _produce_lemma_impl(
        self, word_obj: WordObj, lemmas_freq_list: List[Tuple[str, int]] | None = None
    ):
        morphy_tag = self._get_morphy_tag(word_obj)
        if morphy_tag is None:
            return None, None

        results = self._parse_word(word_obj.form)
        logging.debug(
            "RuLemmatizer: form=%s; pos_tag=%s; vars=%s; variants=%s",
            word_obj.form,
            word_obj.pos_tag,
            len(results),
            results,
        )
        best_morphy_variants = self._find_matching_res(morphy_tag, results, word_obj)
        logging.debug(
            "RuLemmatizer: form=%s; pos_tag=%s; vars=%s; best_variants=%s",
            word_obj.form,
            word_obj.pos_tag,
            len(best_morphy_variants),
            best_morphy_variants,
        )

        if not best_morphy_variants:
            return None, None

        if len(best_morphy_variants) == 1:
            morphy_res = best_morphy_variants[0]
            return self._get_lemma(morphy_res, morphy_tag), morphy_res
        unique_lemmas = set()
        for res in best_morphy_variants:
            unique_lemmas.add(self._get_lemma(res, morphy_tag))

        if len(unique_lemmas) == 1:
            l = list(unique_lemmas)
            return l[0], best_morphy_variants[0]

        if lemmas_freq_list is None:
            morphy_res = best_morphy_variants[0]
            return self._get_lemma(morphy_res, morphy_tag), morphy_res

        cur_most_freq = 0
        cur_lemma = list(unique_lemmas)[0]
        for lemma_var, cnt in lemmas_freq_list:
            if lemma_var in unique_lemmas and cnt > cur_most_freq:
                cur_lemma = lemma_var
                cur_most_freq = cnt

        # TODO
        first_res = best_morphy_variants[0]
        return cur_lemma, first_res

    def produce_lemma(
        self, word_obj: WordObj, lemmas_freq_list: List[Tuple[str, int]] | None = None
    ) -> str | None:
        lemma, _ = self._produce_lemma_impl(word_obj, lemmas_freq_list)
        return lemma

    def _fix_feats_impl(self, pymorphy_res, word_obj: WordObj, stat: Stat):
        if pymorphy_res.tag.gender and (new_gender := _GENDER_MAPPING.get(pymorphy_res.tag.gender)):
            if new_gender is not None and word_obj.gender != new_gender:
                logging.debug(
                    "fixing gender for %s: %s -> %s",
                    word_obj.form,
                    word_obj.gender,
                    new_gender,
                )
                stat.fixed_genders += 1
                word_obj.gender = new_gender

        number = 'plur' if word_obj.number == common.WordNumber.PLUR else 'sing'

        if pymorphy_res.tag.number and number != pymorphy_res.tag.number:
            stat.fixed_plural += 1
            logging.debug(
                "fixing plural for %s: %s -> %s",
                word_obj.form,
                number,
                pymorphy_res.tag.number,
            )
            if pymorphy_res.tag.number == 'plur':
                word_obj.number = common.WordNumber.PLUR
            if pymorphy_res.tag.number == 'sing':
                word_obj.number = common.WordNumber.SING

    def __call__(self, doc_obj: lp_doc.Doc):

        stat = Stat()

        for sent in doc_obj:
            for word_obj in sent:

                word = word_obj.form
                if not word:
                    logging.warning("Lemmatizer: Empty form in the word %s", word_obj)
                    continue
                lemma, pymorphy_res = self._produce_lemma_impl(word_obj)

                if lemma:
                    word_obj.lemma = lemma

                if pymorphy_res is not None and self._opts.fix_feats:
                    self._fix_feats_impl(pymorphy_res, word_obj, stat)

        logging.debug(stat)
