#!/usr/bin/env python
# coding: utf-8

import logging

import pymorphy2

from pylp import common
from pylp import lp_doc
from pylp.word_obj import WordObj
from pylp.common import PosTag, SyntLink
from pylp.common import WordGender


class Stat:
    def __init__(self):
        self.fixed_norms = 0
        self.fixed_genders = 0
        self.fixed_plural = 0
        self.not_found = 0

    def __str__(self):
        return (
            f"fixed_norms: {self.fixed_norms}, fixed_genders: {self.fixed_genders}, "
            f"fixed plural: {self.fixed_plural}, not found: {self.not_found}"
        )


class RuLemmatizerOpts:
    def __init__(self, fix_feats=True):
        self.fix_feats = fix_feats


class RuLemmatizer:
    def __init__(self, opts=RuLemmatizerOpts(), **kwargs):
        self._opts = opts
        self._morph = pymorphy2.MorphAnalyzer()
        self._fix_tags = frozenset(
            [
                PosTag.ADJ,
                PosTag.ADJ_SHORT,
                PosTag.PROPN,
                PosTag.NOUN,
                PosTag.ADV,
                PosTag.PARTICIPLE,
                PosTag.PARTICIPLE_SHORT,
                PosTag.VERB,
            ]
        )

        self._pos_tag_mapping = {
            PosTag.ADJ: 'ADJF',
            PosTag.ADJ_SHORT: 'ADJS',
            PosTag.NOUN: 'NOUN',
            PosTag.PROPN: 'NOUN',
            PosTag.PARTICIPLE: 'PRTF',
            PosTag.PARTICIPLE_SHORT: 'PRTS',
            PosTag.ADV: 'ADVB',
            PosTag.VERB: 'VERB',
        }
        self._gender_mapping = {
            WordGender.MASC: 'masc',
            WordGender.FEM: 'femn',
            WordGender.NEUT: 'neut',
        }

        self._rev_gender_mapping = {v: k for k, v in self._gender_mapping.items()}

    def _find_matching_res(self, morphy_tag, results, word_obj: WordObj):
        # try to find the same norm as our current lemma
        max_matching_score = 0
        parsed_res = None
        for res in results:
            score = 0
            score += word_obj.lemma == res.normal_form
            score += res.tag.POS == morphy_tag
            score += self._gender_mapping.get(word_obj.gender) == res.tag.gender
            score += res.tag.number == (
                'plur' if word_obj.number == common.WordNumber.PLUR else 'sing'
            )
            if score > max_matching_score:
                max_matching_score = score
                parsed_res = res
        return parsed_res

    def _fix_feats_impl(self, pymorphy_res, word_obj: WordObj, stat: Stat):
        gender = word_obj.gender

        if gender is not None and self._gender_mapping[gender] != pymorphy_res.tag.gender:
            g = self._rev_gender_mapping.get(pymorphy_res.tag.gender)
            if g is not None:
                logging.debug(
                    "fixing gender for %s: %s -> %s",
                    word_obj.form,
                    self._gender_mapping[gender],
                    pymorphy_res.tag.gender,
                )
                stat.fixed_genders += 1
                word_obj.gender = g

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

    def _get_lemma(self, pymorphy_res, pos_tag):
        if pos_tag in (PosTag.PARTICIPLE, PosTag.PARTICIPLE_SHORT):
            r = pymorphy_res.inflect({'sing', 'masc', 'nomn'})
            if r is not None:
                return r.word
        return pymorphy_res.normal_form

    def _adjust_propn_pos_tag(self, word_obj: WordObj, parsed_results):
        if word_obj.pos_tag == PosTag.PROPN and word_obj.synt_link in (
            SyntLink.AMOD,
            SyntLink.COMPOUND,
        ):
            print(parsed_results)
            # if word_obj.form not in parsed_cache:
            #     parsed_cache[word_obj.form] = self._morph.parse(word_obj.form)
            # results = parsed_cache[word_obj.form]
            # take the most likely
            pos_tag = None
            for res in parsed_results:
                if res.tag.POS == 'PRTF':
                    pos_tag = PosTag.PARTICIPLE
                elif res.tag.POS == 'ADJF':
                    pos_tag = PosTag.ADJ

            if pos_tag is not None:
                word_obj.pos_tag = pos_tag

    def __call__(self, doc_obj: lp_doc.Doc):
        parsed_cache = {}

        stat = Stat()

        for sent in doc_obj:
            for word_obj in sent:
                if word_obj.pos_tag not in self._fix_tags:
                    continue
                word = word_obj.form
                if not word:
                    logging.warning("Lemmatizer: Empty form in the word %s", word_obj)
                    continue

                if word not in parsed_cache:
                    parsed_cache[word] = self._morph.parse(word)
                results = parsed_cache[word]

                self._adjust_propn_pos_tag(word_obj, results)

                # TODO Can you elaborate on this?
                if all(r.tag.POS == 'INFN' for r in results):
                    continue
                morphy_tag = self._pos_tag_mapping[word_obj.pos_tag]
                pymorphy_res = self._find_matching_res(morphy_tag, results, word_obj)
                stat.not_found += pymorphy_res is None

                if pymorphy_res is not None:
                    lemma = self._get_lemma(pymorphy_res, word_obj.pos_tag)
                    if lemma and word_obj.lemma != lemma:
                        logging.debug(
                            "fixing norm for form %s: %s -> %s", word, word_obj.lemma, lemma
                        )
                        stat.fixed_norms += 1
                        word_obj.lemma = lemma

                if not word_obj.lemma:
                    logging.warning("Lemmatizer: Empty lemma in the word %s", word_obj)
                    continue

                if pymorphy_res is not None and self._opts.fix_feats:
                    self._fix_feats_impl(pymorphy_res, word_obj, stat)

        logging.debug(stat)
