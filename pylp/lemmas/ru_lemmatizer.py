#!/usr/bin/env python
# coding: utf-8

import logging

import pymorphy2

from pylp.common import Attr
from pylp.common import PosTag
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
            [PosTag.ADJ, PosTag.NOUN, PosTag.PARTICIPLE, PosTag.ADV, PosTag.VERB]
        )

        self._pos_tag_mapping = {
            PosTag.ADJ: 'ADJF',
            PosTag.NOUN: 'NOUN',
            PosTag.PARTICIPLE: 'PRTF',
            PosTag.ADV: 'ADVB',
            PosTag.VERB: 'VERB',
        }
        self._gender_mapping = {
            WordGender.MASC: 'masc',
            WordGender.FEM: 'femn',
            WordGender.NEUT: 'neut',
        }

        self._rev_gender_mapping = {v: k for k, v in self._gender_mapping.items()}

    def _find_matching_res(self, morphy_tag, results, current_norm):
        # try to found the same norm as our current lemma
        if current_norm is not None:
            for res in results:
                if res.tag.POS == morphy_tag and res.normal_form == current_norm:
                    # logging.debug("Found the same norm for res: %s", res)
                    return res
        for res in results:
            if res.tag.POS == morphy_tag:
                return res
        return None

    def _fix_feats_impl(self, pymorphy_res, word_obj, stat: Stat):
        gender = word_obj.get(Attr.GENDER)

        if gender is not None and self._gender_mapping[gender] != pymorphy_res.tag.gender:
            g = self._rev_gender_mapping.get(pymorphy_res.tag.gender)
            if g is not None:
                logging.debug(
                    "fixing gender for %s: %s -> %s",
                    word_obj[Attr.WORD_FORM],
                    self._gender_mapping[gender],
                    pymorphy_res.tag.gender,
                )
                stat.fixed_genders += 1
                word_obj[Attr.GENDER] = g

        number = 'plur' if Attr.PLURAL in word_obj else 'sing'

        if pymorphy_res.tag.number and number != pymorphy_res.tag.number:
            stat.fixed_plural += 1
            logging.debug(
                "fixing plural for %s: %s -> %s",
                word_obj[Attr.WORD_FORM],
                number,
                pymorphy_res.tag.number,
            )
            if pymorphy_res.tag.number == 'plur':
                word_obj[Attr.PLURAL] = 1
            if pymorphy_res.tag.number == 'sing':
                del word_obj[Attr.PLURAL]

    def _get_lemma(self, pymorphy_res, pos_tag):
        if pos_tag == PosTag.PARTICIPLE:
            r = pymorphy_res.inflect({'sing', 'masc', 'nomn'})
            if r is not None:
                return r.word
        return pymorphy_res.normal_form

    def __call__(self, doc_obj):
        parsed_cache = {}

        stat = Stat()

        for sent in doc_obj['sents']:
            for word_obj in sent:
                pos_tag = word_obj.get(Attr.POS_TAG)
                if pos_tag not in self._fix_tags:
                    continue
                word = word_obj[Attr.WORD_FORM]
                if word not in parsed_cache:
                    parsed_cache[word] = self._morph.parse(word)
                results = parsed_cache[word]

                # TODO Can you elaborate on this?
                if all(r.tag.POS == 'INFN' for r in results):
                    continue
                morphy_tag = self._pos_tag_mapping[pos_tag]
                current_norm = word_obj.get(Attr.WORD_LEMMA)
                pymorphy_res = self._find_matching_res(morphy_tag, results, current_norm)
                stat.not_found += pymorphy_res is None

                if pymorphy_res is not None:
                    lemma = self._get_lemma(pymorphy_res, pos_tag)
                    if current_norm != lemma:
                        logging.debug(
                            "fixing norm for form %s: %s -> %s", word, current_norm, lemma
                        )
                        stat.fixed_norms += 1
                        word_obj[Attr.WORD_LEMMA] = lemma

                if pymorphy_res is not None and self._opts.fix_feats:
                    self._fix_feats_impl(pymorphy_res, word_obj, stat)

        logging.debug(stat)
