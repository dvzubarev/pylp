#!/usr/bin/env python
# coding: utf-8


import logging

import pymorphy2
import libpyexbase


from pylp.filtratus import Filtratus
from pylp.common import Attr
from pylp.common import PosTag
from pylp.common import SyntLink
from pylp.common import WordGender
from pylp.common import PREP_WHITELIST


class PostProcessor:
    def __init__(self, kinds, **proc_kwargs):
        self._procs = {}
        for k in kinds:
            kwargs = proc_kwargs.get(k, {})
            self._procs[k] = create_postprocessor(k, **kwargs)
            logging.info("Loading %s postprocessor!", k)

    def __call__(self, kinds, text, doc_obj, **proc_params):
        for k in kinds:
            if k not in self._procs:
                raise RuntimeError("PostProcessor %s is not loaded!" % k)

            params_key = k + '_params'
            params = proc_params.get(params_key, {})
            self._procs[k](text, doc_obj, **params)


def create_postprocessor(kind, **kwargs):
    if kind == Filtratus.name:
        return Filtratus(**kwargs)
    if kind == PrepositionCompressor.name:
        return PrepositionCompressor(**kwargs)
    if kind == FragmentsMaker.name:
        return FragmentsMaker(**kwargs)
    if kind == WordLangDetector.name:
        return WordLangDetector(**kwargs)
    if kind == FixNorms.name:
        return FixNorms(**kwargs)
    raise RuntimeError("Unknown postprocessor: %s" % kind)


class AbcPostProcessor:
    def __call__(self, text, doc_obj):
        raise NotImplementedError("ABC")


class PrepositionCompressor(AbcPostProcessor):
    name = "preposition_compressor"

    def __init__(self, **kwargs):
        pass

    def __call__(self, text, doc_obj):
        for s in doc_obj['sents']:
            self._proc_sent(s, doc_obj['word_ids'])

    def _proc_sent(self, sent, word_ids):
        for pos, wobj in enumerate(sent):

            if (
                wobj.get(Attr.POS_TAG) == PosTag.ADP
                and wobj.get(Attr.SYNTAX_LINK_NAME) == SyntLink.CASE
            ):
                head_offs = wobj.get(Attr.SYNTAX_PARENT)
                if not head_offs:
                    continue
                head_pos = pos + head_offs
                head_obj = sent[head_pos]

                head_obj[Attr.PREP_MOD] = wobj[Attr.WORD_NUM]
                if word_ids[wobj[Attr.WORD_NUM]] in PREP_WHITELIST:
                    head_obj[Attr.PREP_WHITE_LIST] = True


class FragmentsMaker(AbcPostProcessor):
    name = "fragments_maker"

    def __init__(self):
        pass

    def _sent_chars_cnt(self, doc_obj, sent):
        return sum(len(doc_obj['words'][wobj[Attr.WORD_NUM]]) for wobj in sent)

    def __call__(
        self,
        text,
        doc_obj,
        max_fragment_length=20,
        max_chars_cnt=5_000,
        min_sent_length=4,
        overlap=2,
    ):
        good_sents = []
        fragments = []
        fragment_size = 0
        fragment_chars_cnt = 0
        fragment_begin_no = 0

        num = -1
        for num, sent in enumerate(doc_obj['sents']):
            if max_chars_cnt:
                fragment_chars_cnt += self._sent_chars_cnt(doc_obj, sent)

            if len(sent) >= min_sent_length:
                fragment_size += 1
                good_sents.append(num)

            if fragment_size >= max_fragment_length or (
                max_chars_cnt and fragment_chars_cnt > max_chars_cnt
            ):

                fragments.append((fragment_begin_no, num))
                if (
                    overlap
                    and good_sents
                    and good_sents[-min(overlap, len(good_sents))] > fragment_begin_no
                ):
                    fragment_begin_no = good_sents[-min(overlap, len(good_sents))]
                else:
                    fragment_begin_no = num + 1

                fragment_size = overlap
                if max_chars_cnt:
                    fragment_chars_cnt = sum(
                        self._sent_chars_cnt(doc_obj, s)
                        for s in doc_obj['sents'][fragment_begin_no : num + 1]
                    )

        end = len(doc_obj['sents']) - 1
        cur_end = fragments[-1][1] if fragments else -1
        if num != -1 and fragment_begin_no <= end and cur_end != end:
            fragments.append((fragment_begin_no, end))

        logging.debug("created %d fragments", len(fragments))
        doc_obj['fragments'] = fragments


class WordLangDetector(AbcPostProcessor):
    name = "word_lang_detector"

    def __init__(self, **kwargs):
        pass

    def __call__(self, text, doc_obj):
        doc_lang = doc_obj['lang']
        langs = libpyexbase.lang_of_words(doc_obj['words'])

        for sent in doc_obj['sents']:
            for word_obj in sent:
                word_lang = langs[word_obj[Attr.WORD_NUM]]
                if word_lang != doc_lang:
                    word_obj[Attr.LANG] = word_lang


class FixNorms(AbcPostProcessor):
    name = "fix_norms"

    def __init__(self, **kwargs):
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

    def _find_norm(self, current_norm, morphy_tag, results):
        for res in results:
            if res.tag.POS == morphy_tag and res.normal_form == current_norm:
                # logging.debug("Found the same norm for res: %s", res)
                return None
        for res in results:
            if res.tag.POS == morphy_tag:
                return res.normal_form
        return None

    def __call__(self, text, doc_obj):
        words = doc_obj['words']
        parsed_cache = {}

        fixed_norms = fixed_gender = fixed_plural = not_found = 0

        for sent in doc_obj['sents']:
            for word_obj in sent:
                word_num = word_obj[Attr.WORD_NUM]
                pos_tag = word_obj.get(Attr.POS_TAG)
                if pos_tag not in self._fix_tags:
                    continue
                off = word_obj[Attr.OFFSET]
                word = text[off : off + word_obj[Attr.LENGTH]]
                if word not in parsed_cache:
                    parsed_cache[word] = self._morph.parse(word)
                results = parsed_cache[word]

                if all(r.tag.POS == 'INFN' for r in results):
                    continue
                morphy_tag = self._pos_tag_mapping[pos_tag]
                norm = self._find_norm(words[word_num], morphy_tag, results)
                if norm is not None:
                    logging.debug(
                        "fixing norm for form %s: %s -> %s (%s)",
                        word,
                        words[word_num],
                        norm,
                        word_num,
                    )
                    fixed_norms += 1
                    words[word_num] = norm

                found = False
                for res in results:
                    if res.tag.POS == morphy_tag:
                        found = True

                        gender = word_obj.get(Attr.GENDER)

                        if gender is not None and self._gender_mapping[gender] != res.tag.gender:
                            g = self._rev_gender_mapping.get(res.tag.gender)
                            if g is not None:
                                logging.debug(
                                    "fixing gender for %s: %s -> %s",
                                    words[word_num],
                                    self._gender_mapping[gender],
                                    res.tag.gender,
                                )
                                fixed_gender += 1
                                word_obj[Attr.GENDER] = g

                        number = 'plur' if Attr.PLURAL in word_obj else 'sing'

                        if res.tag.number and number != res.tag.number:
                            fixed_plural += 1
                            logging.debug(
                                "fixing plural for %s: %s -> %s", word, number, res.tag.number
                            )
                            if res.tag.number == 'plur':
                                word_obj[Attr.PLURAL] = 1
                            if res.tag.number == 'sing':
                                del word_obj[Attr.PLURAL]

                        break
                not_found += not found
        logging.info(
            "Fixed %s norms, %s genders, %s plurs, not found forms %s",
            fixed_norms,
            fixed_gender,
            fixed_plural,
            not_found,
        )
