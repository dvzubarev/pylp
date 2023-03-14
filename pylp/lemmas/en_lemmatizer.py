#!/usr/bin/env python
# coding: utf-8

import logging
import pickle
from typing import List, Set, Tuple
import os
import gzip
import json

from pylp import lp_doc
from pylp.lemmas.abc_lemmatizer import AbcLemmatizer
from pylp.word_obj import WordObj
from pylp.common import PosTag, WordNumber, WordDegree, WordPerson, WordTense


_WN_POS_TAG_MAPPING = {
    PosTag.PROPN: 'n',
    PosTag.NOUN: 'n',
    PosTag.VERB: 'v',
    PosTag.PARTICIPLE: 'v',
    PosTag.GERUND: 'v',
    PosTag.ADJ: 'a',
    PosTag.ADV: 'r',
}
_NOUN_PLURAL_RULES = [
    ("ches", "ch"),
    ("shes", "sh"),
    ("ces", "x"),
    ("ses", "s"),
    ("ives", "ife"),
    ("ves", "f"),
    ("xes", "x"),
    ("xes", "xis"),
    ("zes", "z"),
    ("ies", "y"),
    ("s", ""),
    ("men", "man"),
]

_VERB_3RD_PERSON_RULES = [
    ("es", ""),
    ("ies", "y"),
    ("s", ""),
    ("es", "e"),
]
_VERB_PAST_RULES = [
    ("ed", ""),
    ("ed", "e"),
]
_VERB_GERUND_RULES = [
    ("ing", ""),
    ("ing", "e"),
]
_ADJ_COMP_RULES = [
    ("er", ""),
    ("er", "e"),
]
_ADJ_SUP_RULES = [
    ("est", ""),
    ("est", "e"),
]


class EnLemmatizer(AbcLemmatizer):
    def __init__(self, **_):
        self._res_dir = os.environ.get('PYLP_RESOURCES_DIR')
        if self._res_dir is None:
            raise RuntimeError("Env var PYLP_RESOURCES_DIR is not set!")

        with gzip.open(f'{self._res_dir}/lemma.en.exc.json.gz') as fp:
            self._excep_dict = json.load(fp)
        mapping = {'adj': PosTag.ADJ, 'adv': PosTag.ADV, 'noun': PosTag.NOUN, 'verb': PosTag.VERB}
        self._excep_dict = {
            mapping[k]: {form: lemmas[0] for form, lemmas in v.items()}
            for k, v in self._excep_dict.items()
        }

        self._known_lemmas = None

    def _get_known_lemmas(self):
        if self._known_lemmas is None:
            with gzip.open(f'{self._res_dir}/lemma.en.known_lemmas.pickle.gz') as fp:
                self._known_lemmas = pickle.load(fp)
        return self._known_lemmas

    def _apply_rules(self, word, rules):
        candidates = []
        unique_candidates = set()
        for suffix, repl in rules:
            if word.endswith(suffix) and len(suffix) < len(word):
                candidate = f'{word[:-len(suffix)]}{repl}'
                candidates.append(candidate)
                unique_candidates.add(candidate)
        return candidates, unique_candidates

    def produce_lemma(
        self, word_obj: WordObj, lemmas_freq_list: List[Tuple[str, int]] | None = None
    ) -> str | None:
        if word_obj.form is None:
            return None
        word = word_obj.form.lower()

        # try to look up in exceptions
        pos_tag = word_obj.pos_tag
        if pos_tag == PosTag.PROPN:
            pos_tag = PosTag.NOUN
        if (exceptions_dict := self._excep_dict.get(pos_tag)) is not None and (
            lemma := exceptions_dict.get(word)
        ) is not None:
            logging.debug(
                "form=%s; pos_tag=%s; exception_found=%s",
                word_obj.form,
                word_obj.pos_tag,
                lemma,
            )
            return lemma

        candidates = []
        unique_candidates = set()

        match word_obj:
            case WordObj(pos_tag=(PosTag.NOUN | PosTag.PROPN), number=WordNumber.PLUR):
                candidates, unique_candidates = self._apply_rules(word, _NOUN_PLURAL_RULES)
            case WordObj(pos_tag=PosTag.ADJ, degree=WordDegree.CMP):
                candidates, unique_candidates = self._apply_rules(word, _ADJ_COMP_RULES)
            case WordObj(pos_tag=PosTag.ADJ, degree=WordDegree.SUP):
                candidates, unique_candidates = self._apply_rules(word, _ADJ_SUP_RULES)
            case WordObj(pos_tag=PosTag.VERB, tense=WordTense.PRES, person=WordPerson.III):
                candidates, unique_candidates = self._apply_rules(word, _VERB_3RD_PERSON_RULES)
            case WordObj(pos_tag=(PosTag.VERB | PosTag.PARTICIPLE), tense=WordTense.PAST):
                candidates, unique_candidates = self._apply_rules(word, _VERB_PAST_RULES)
            case WordObj(pos_tag=PosTag.GERUND) | WordObj(
                pos_tag=PosTag.PARTICIPLE, tense=WordTense.PRES
            ):
                candidates, unique_candidates = self._apply_rules(word, _VERB_GERUND_RULES)

        logging.debug(
            "form=%s; pos_tag=%s; candidates=%s",
            word_obj.form,
            word_obj.pos_tag,
            candidates,
        )

        if not candidates:
            return word

        return self._resolve_candidates(word_obj, candidates, unique_candidates, lemmas_freq_list)

    def _resolve_candidates(
        self,
        word_obj: WordObj,
        candidates: List[str],
        unique_candidates: Set[str],
        lemmas_freq_list: List[Tuple[str, int]] | None = None,
    ):
        if len(unique_candidates) == 1:
            return candidates[0]

        if lemmas_freq_list is not None:
            cur_most_freq = 0
            cur_lemma = None
            for lemma_var, cnt in lemmas_freq_list:
                if lemma_var in unique_candidates and cnt > cur_most_freq:
                    cur_lemma = lemma_var
                    cur_most_freq = cnt
            if cur_lemma is not None:
                return cur_lemma

        known_lemmas = self._get_known_lemmas()
        wn_pos = _WN_POS_TAG_MAPPING.get(word_obj.pos_tag, [])
        for candidate in candidates:
            if (wn_pos, candidate) in known_lemmas:
                return candidate

        return candidates[0]

    def __call__(self, doc_obj: lp_doc.Doc):
        for sent in doc_obj:
            for word_obj in sent:

                word = word_obj.form
                if not word:
                    logging.warning("Empty form in the word %s", word_obj)
                    continue
                lemma = self.produce_lemma(word_obj)

                if lemma:
                    word_obj.lemma = lemma
