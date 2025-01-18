#!/usr/bin/env python
# coding: utf-8

import gzip
import json
import importlib.resources
from typing import List, MutableMapping, Mapping, Optional
import collections

import pymorphy2

from pylp.common import (
    Lang,
    PosTag,
    WordGender,
    WordNumber,
    WordVoice,
    WordTense,
    WordCase,
    SyntLink,
)
from pylp import lp_doc
from pylp.phrases.phrase import Phrase
from pylp.phrases.builder import MWE_RELS
from pylp.word_obj import WordObj


# * Abstract classes


class Inflector:
    def inflect_head(self, phrase: Phrase, sent: lp_doc.Sent, head_pos):
        raise NotImplementedError("inflect head is not implemented")

    def inflect_pair(self, phrase: Phrase, sent: lp_doc.Sent, head_pos, mod_pos):
        raise NotImplementedError("inflect pair is not implemented")

    def inflect_phrase(self, phrase: Phrase, sent: lp_doc.Sent):
        raise NotImplementedError("inflect phrase is not implemented")


class VerbExcpForms:
    __slots__ = ('pres_part', 'past_part')

    def __init__(self, pres_part: Optional[str] = None, past_part: Optional[str] = None) -> None:
        self.pres_part = pres_part
        self.past_part = past_part

    def to_json(self):
        return {'prp': self.pres_part, 'pap': self.past_part}

    @classmethod
    def from_json(cls, obj):
        return cls(pres_part=obj.get('prp'), past_part=obj.get('pap'))

    def __repr__(self) -> str:
        return f"VerbExcpForms(pres_part={self.pres_part}, past_part={self.past_part})"


# * API


def inflect_phrases(phrases: List[Phrase], sent: lp_doc.Sent, text_lang):
    for phrase in phrases:
        inflect_phrase(phrase, sent, text_lang)


def inflect_phrase(phrase: Phrase, sent: lp_doc.Sent, text_lang, cache_max_size: int = -1):
    """
    When cache_max_size == 0, use cache with unbounded size, when its value <= -1 do not use cache at all.
    In other cases cache_max_size is the number of phrases that are stored in the cache at the same time.
    """
    cache_key, result = _cache_lookup(phrase, sent, cache_max_size)
    if result is not None:
        phrase.get_words()[:] = result
        return

    word_lang_func = lambda o: text_lang if o.lang is None else o.lang
    word_langs = [word_lang_func(sent[i]) for i in phrase.get_sent_pos_list()]
    if any(l == Lang.RU for l in word_langs):
        inflect_ru_phrase(phrase, sent)
    elif any(l == Lang.EN for l in word_langs):
        inflect_en_phrase(phrase, sent)
    else:
        raise RuntimeError(f"Unsupported language in phrase to inflect: {phrase}")

    _put_to_cache(cache_key, phrase.get_words(), cache_max_size)


def inflect_ru_phrase(phrase: Phrase, sent: lp_doc.Sent):
    inflector = _get_ru_inflector()
    inflector.inflect_phrase(phrase, sent)


def inflect_en_phrase(phrase: Phrase, sent: lp_doc.Sent):
    inflector = _get_en_inflector()
    inflector.inflect_phrase(phrase, sent)


# * Implementation
# ** Common


def _capitalize(word):
    if word.isupper():
        return word
    return word.capitalize()


class BaseInflector(Inflector):
    def __init__(self) -> None:
        super().__init__()
        self._inflected = []

    def _reset(self):
        self._inflected = []

    def _init(self, phrase: Phrase, sent: lp_doc.Sent):
        self._inflected = [False] * phrase.size_with_preps()

    def inflect_phrase(self, phrase: Phrase, sent: lp_doc.Sent):
        try:
            self._init(phrase, sent)
            self._inflect_phrase_impl(phrase, sent, phrase.get_head_pos())

        finally:
            self._reset()

    def _inflect_phrase_impl(self, phrase: Phrase, sent: lp_doc.Sent, head_pos):
        if not self._inflected[head_pos]:
            self.inflect_head(phrase, sent, head_pos)
            self._inflected[head_pos] = True

        for mod_pos, l in enumerate(phrase.get_deps()):
            if not self._inflected[mod_pos] and l and mod_pos + l == head_pos:
                # this is modificator
                self.inflect_pair(phrase, sent, head_pos, mod_pos)
                self._inflected[mod_pos] = True
                # recursively inflect modificators of inflected modificator
                self._inflect_phrase_impl(phrase, sent, mod_pos)


# ** Ru impl

RU_INFLECTOR = None


def _get_ru_inflector():
    global RU_INFLECTOR
    if RU_INFLECTOR is None:
        RU_INFLECTOR = RuInflector()
    return RU_INFLECTOR


class RuInflector(BaseInflector):
    def __init__(self):
        super().__init__()

        self._pymorphy = pymorphy2.MorphAnalyzer()
        self._parsed_cache = {}
        self._max_cache_size = 20_000

        self._cases: List[WordCase] = []
        self._case_mapping = {
            WordCase.NOM: 'nomn',
            WordCase.GEN: 'gent',
            WordCase.ACC: 'accs',
            WordCase.DAT: 'datv',
            WordCase.INS: 'ablt',
            WordCase.LOC: 'loct',
            WordCase.VOC: 'voct',
        }

    def _reset(self):
        super()._reset()
        self._cases = []

    def _init(self, phrase: Phrase, sent: lp_doc.Sent):
        super()._init(phrase, sent)
        self._cases = [WordCase.NOM] * phrase.size_with_preps()

    def inflect_head(self, phrase: Phrase, sent: lp_doc.Sent, head_pos):
        # We can only change number of a word
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]
        phrase_words = phrase.get_words()

        if head_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):
            if head_obj.number == WordNumber.PLUR:
                form = self._pymorphy_inflect(phrase_words[head_pos], "NOUN", {'number': 'plur'})
                if form is not None:
                    phrase_words[head_pos] = form

        if head_obj.pos_tag == PosTag.PROPN:
            phrase_words[head_pos] = _capitalize(phrase_words[head_pos])

    def _inflect_to_case(self, word, word_obj: WordObj):
        number = 'plur' if word_obj.number == WordNumber.PLUR else 'sing'
        if word_obj.case is None:
            return None, None

        case = self._case_mapping.get(word_obj.case)
        if case is None:
            return None, None
        feats = {'number': number, 'case': case}
        if (
            word_obj.gender is not None
            and (gender := self._gender2pymorphy(word_obj.gender)) is not None
        ):
            feats['gender'] = gender

        form = self._pymorphy_inflect(word, "NOUN", feats)
        return form, word_obj.case

    def _resolve_conj_link(self, pos: int, word_obj: WordObj, sent: lp_doc.Sent):
        while word_obj.parent_offs and word_obj.synt_link == SyntLink.CONJ:
            pos += word_obj.parent_offs
            word_obj = sent[pos]
        return word_obj.synt_link

    def _inflect_noun_noun(
        self,
        phrase: Phrase,
        head_pos,
        head_obj: WordObj,
        mod_pos,
        mod_obj: WordObj,
        sent: lp_doc.Sent,
    ):
        phrase_words = phrase.get_words()
        form = None
        link = mod_obj.synt_link
        if link == SyntLink.CONJ:
            mod_sent_pos = phrase.get_sent_pos_list()[mod_pos]
            link = self._resolve_conj_link(mod_sent_pos, mod_obj, sent)

        if link == SyntLink.NMOD or link in MWE_RELS:
            form, case = self._inflect_to_case(phrase_words[mod_pos], mod_obj)
            if case is not None:
                self._cases[mod_pos] = case

        if mod_obj.pos_tag == PosTag.PROPN:
            if form is None:
                form = phrase_words[mod_pos]

            form = _capitalize(form)

        if form is not None:
            phrase_words[mod_pos] = form

    def inflect_pair(self, phrase: Phrase, sent: lp_doc.Sent, head_pos, mod_pos):
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]
        mod_sent_pos = phrase.get_sent_pos_list()[mod_pos]
        mod_obj = sent[mod_sent_pos]

        phrase_words = phrase.get_words()
        if head_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):

            if mod_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):
                self._inflect_noun_noun(
                    phrase,
                    head_pos=head_pos,
                    head_obj=head_obj,
                    mod_pos=mod_pos,
                    mod_obj=mod_obj,
                    sent=sent,
                )
            elif mod_obj.pos_tag in (PosTag.ADJ, PosTag.PARTICIPLE):
                number = 'plur' if head_obj.number == WordNumber.PLUR else 'sing'
                feats = {'number': number}
                if number != 'plur':
                    gender = self._gender2pymorphy(head_obj.gender)
                    if gender is not None:
                        feats['gender'] = gender

                feats['case'] = self._case_mapping[self._cases[head_pos]]

                if mod_obj.pos_tag == PosTag.ADJ:
                    form = self._pymorphy_inflect(phrase_words[mod_pos], 'ADJF', feats)
                else:
                    form = self._pymorphy_inflect(phrase_words[mod_pos], 'PRTF', feats, mod_obj)

                if form is not None:
                    phrase_words[mod_pos] = form

    def _gender2pymorphy(self, gender):
        if gender == WordGender.FEM:
            return "femn"
        if gender == WordGender.MASC:
            return "masc"
        if gender == WordGender.NEUT:
            return "neut"
        return None

    def _pymorphy_find_participle(self, inf, mod_obj: Optional[WordObj] = None):
        if mod_obj is None:
            return None

        voice = mod_obj.voice if mod_obj.voice is not None else WordVoice.ACT
        tense = mod_obj.tense if mod_obj.tense is not None else WordTense.PRES

        if voice == WordVoice.ACT:
            voice = 'actv'
        elif voice == WordVoice.PASS:
            voice = 'pssv'
        else:
            return None
        if tense == WordTense.PRES:
            tense = 'pres'
        elif tense == WordTense.PAST:
            tense = 'past'
        else:
            return None

        for l in inf.lexeme:
            if (
                l.tag.POS == 'PRTF'
                and l.tag.voice == voice
                and l.tag.tense == tense
                and l.tag.case == 'nomn'
            ):
                return l
        return None

    def _parse_word(self, word):
        if word not in self._parsed_cache:
            if len(self._parsed_cache) > self._max_cache_size:
                self._parsed_cache.clear()
            self._parsed_cache[word] = self._pymorphy.parse(word)
        return self._parsed_cache[word]

    def _pymorphy_inflect(self, word: str, tag: str, feats_dict, mod_obj: Optional[WordObj] = None):
        results = self._parse_word(word)

        parsed = None

        for res in results:
            if res.tag.POS == tag and res.tag.case == 'nomn':
                parsed = res
                break
        if parsed is None and tag == 'PRTF':
            for res in results:
                if res.tag.POS == 'INFN':
                    parsed = self._pymorphy_find_participle(res, mod_obj)
                    if parsed is not None:
                        break

        if parsed is not None:
            if parsed.tag.gender is None and 'gender' in feats_dict:
                del feats_dict['gender']

            inflected = parsed.inflect(frozenset(feats_dict.values()))

            if inflected is not None:
                return inflected.word

        return None


# ** En Impl

EN_INFLECTOR = None


def _get_en_inflector():
    global EN_INFLECTOR
    if EN_INFLECTOR is None:
        EN_INFLECTOR = EnInflector()
    return EN_INFLECTOR


EN_ALREADY_PLUR = frozenset(
    [
        'people',
        'fish',
        'sheep',
        'deer',
        'moose',
        'aircraft',
        'rights',
        'statistics',
        'raybans',
        'belongings',
        'binoculars',
        'boxers',
        'briefs',
        'clothes',
        'congratulations',
        'dislikes',
        'earnings',
        'glasses',
        'goggles',
        'goods',
        'headphones',
        'jeans',
        'knickers',
        'likes',
        'outskirts',
        'panties',
        'pants',
        'pliers',
        'premises',
        'pyjamas',
        'savings',
        'scissors',
        'shorts',
        'stairs',
        'sunglasses',
        'surroundings',
        'thanks',
        'tights',
        'tongs',
        'trousers',
        'tweezers',
    ]
)


class EnInflector(BaseInflector):
    def __init__(self):
        super().__init__()
        p = importlib.resources.files('pylp.phrases.data').joinpath('en_lemma_exc.json.gz')
        with p.open('rb') as bf:
            gf = gzip.GzipFile(fileobj=bf)
            excep_dict = json.load(
                gf, object_hook=lambda d: d if 'pap' not in d else VerbExcpForms.from_json(d)
            )

        self._noun_excep_dict: MutableMapping[str, str] = excep_dict['noun']
        # TODO there is no these words in spacy's en_lemma_exc.json
        self._noun_excep_dict['woman'] = 'women'
        self._verb_excep_dict: Mapping[str, VerbExcpForms] = excep_dict['verb']

    def _inflect_plural(self, lemma: str) -> Optional[str]:
        if not lemma:
            return None
        if lemma in EN_ALREADY_PLUR:
            return lemma
        form = self._noun_excep_dict.get(lemma)
        if form is not None:
            return form

        last_letter = lemma[-1]
        if last_letter in ('s', 'x', 'z'):
            return lemma + 'es'

        if len(lemma) > 1:
            last_two_letters = lemma[-2:]
            if last_two_letters in ('sh', 'ch'):
                return lemma + 'es'

            if last_letter == 'y' and lemma[-2] not in 'aeiou':
                return lemma[:-1] + 'ies'

        return lemma + 's'

    def inflect_head(self, phrase: Phrase, sent: lp_doc.Sent, head_pos):
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]

        phrase_words = phrase.get_words()
        if head_obj.number == WordNumber.PLUR:
            form = self._inflect_plural(phrase_words[head_pos])
            if form is not None:
                phrase_words[head_pos] = form

        if head_obj.pos_tag == PosTag.PROPN:
            phrase_words[head_pos] = _capitalize(phrase_words[head_pos])

    def inflect_pair(self, phrase: Phrase, sent: lp_doc.Sent, head_pos, mod_pos):
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]
        mod_sent_pos = phrase.get_sent_pos_list()[mod_pos]
        mod_obj = sent[mod_sent_pos]

        phrase_words = phrase.get_words()
        current_lemma = phrase_words[mod_pos]
        form = None
        if head_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):

            if mod_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):
                if mod_obj.number == WordNumber.PLUR:
                    form = self._inflect_plural(current_lemma)
                if mod_obj.pos_tag == PosTag.PROPN:
                    if form is None:
                        form = current_lemma
                    form = _capitalize(form)

            elif (
                mod_obj.pos_tag == PosTag.PARTICIPLE and mod_obj.tense in (None, WordTense.PRES)
            ) or mod_obj.pos_tag == PosTag.GERUND:
                # check exceptions
                if (
                    verb_excp_form := self._verb_excep_dict.get(current_lemma)
                ) and verb_excp_form.pres_part:
                    form = verb_excp_form.pres_part
                else:
                    # inflect by rules
                    if current_lemma.endswith('ie'):
                        form = current_lemma[:-2] + 'ying'
                    elif current_lemma.endswith('e'):
                        form = current_lemma[:-1] + 'ing'
                    elif not current_lemma.endswith('ing'):
                        form = current_lemma + 'ing'
            elif mod_obj.pos_tag == PosTag.PARTICIPLE and mod_obj.tense == WordTense.PAST:
                # check exceptions
                if (
                    verb_excp_form := self._verb_excep_dict.get(current_lemma)
                ) and verb_excp_form.past_part:
                    form = verb_excp_form.past_part
                else:
                    # inflect by rules
                    if current_lemma.endswith('e'):
                        form = current_lemma + 'd'
                    elif not current_lemma.endswith('ed'):
                        form = current_lemma + 'ed'

        if form is not None:
            phrase_words[mod_pos] = form


# * Cache
#
_CACHE = collections.OrderedDict()
_CACHE_HITS = 0
_CACHE_MISSES = 0


def get_inflect_cache_info():
    return len(_CACHE), _CACHE_HITS, _CACHE_MISSES


def _cache_lookup(phrase: Phrase, sent: lp_doc.Sent, cache_max_size: int):
    global _CACHE_HITS, _CACHE_MISSES
    if cache_max_size <= -1:
        return tuple(), None

    parts = []
    for wp in phrase.get_sent_pos_list():
        word_obj = sent[wp]
        parts.append(
            (
                word_obj.word_id,
                word_obj.pos_tag,
                word_obj.case,
                word_obj.number,
                word_obj.gender,
                word_obj.voice,
                word_obj.tense,
            )
        )
    key = tuple(parts)
    result = _CACHE.get(key)
    if result is not None:
        _CACHE_HITS += 1
        _CACHE.move_to_end(key)
    else:
        _CACHE_MISSES += 1

    return key, result


def _put_to_cache(key: tuple, result, cache_max_size: int):
    if cache_max_size <= -1:
        return
    _CACHE[key] = result
    if len(_CACHE) > cache_max_size:
        _CACHE.popitem(last=False)
