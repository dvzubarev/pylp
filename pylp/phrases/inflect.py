#!/usr/bin/env python
# coding: utf-8

import gzip
import json
import importlib.resources
from typing import List, Mapping, Optional

import pymorphy2

from pylp.common import (
    Attr,
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
from pylp.word_obj import WordObj


# Abstract classes
class Inflector:
    def inflect_head(self, phrase: Phrase, sent: lp_doc.Sent, head_pos):
        raise NotImplementedError("inflect head is not implemented")

    def inflect_pair(self, phrase: Phrase, sent: lp_doc.Sent, head_pos, mod_pos):
        raise NotImplementedError("inflect pair is not implemented")


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


# API


def inflect_phrases(phrases: List[Phrase], sent: lp_doc.Sent, text_lang):
    for phrase in phrases:
        inflect_phrase(phrase, sent, text_lang)


def inflect_phrase(phrase: Phrase, sent: lp_doc.Sent, text_lang):
    word_lang_func = lambda o: text_lang if o.lang is None else o.lang
    word_langs = [word_lang_func(sent[i]) for i in phrase.get_sent_pos_list()]
    if any(l == Lang.RU for l in word_langs):
        return inflect_ru_phrase(phrase, sent)
    if any(l == Lang.EN for l in word_langs):
        return inflect_en_phrase(phrase, sent)

    raise RuntimeError(f"Unsupported language in phrase to inflect: {phrase}")


def inflect_ru_phrase(phrase: Phrase, sent: lp_doc.Sent):
    _inflect_mods_of_head(phrase, sent, phrase.get_head_pos(), inflector=_get_ru_inflector())


def inflect_en_phrase(phrase: Phrase, sent: lp_doc.Sent):
    _inflect_mods_of_head(phrase, sent, phrase.get_head_pos(), inflector=_get_en_inflector())


# Implementation


def _inflect_mods_of_head(
    phrase: Phrase,
    sent: lp_doc.Sent,
    head_pos,
    inflector: Inflector,
    inflected=None,
):
    if inflected is None:
        inflected = [False] * phrase.size()

    if not inflected[head_pos]:
        inflector.inflect_head(phrase, sent, head_pos)
        inflected[head_pos] = True

    for mod_pos, l in enumerate(phrase.get_deps()):
        if not inflected[mod_pos] and l and mod_pos + l == head_pos:
            # this is modificator
            inflector.inflect_pair(phrase, sent, head_pos, mod_pos)
            inflected[mod_pos] = True
            # recursively inflect modificators of inflected modificator
            _inflect_mods_of_head(phrase, sent, mod_pos, inflector, inflected)


RU_INFLECTOR = None


def _get_ru_inflector():
    global RU_INFLECTOR
    if RU_INFLECTOR is None:
        RU_INFLECTOR = RuInflector()
    return RU_INFLECTOR


class RuInflector(Inflector):
    def __init__(self):
        self._pymorphy = pymorphy2.MorphAnalyzer()

    def inflect_head(self, phrase: Phrase, sent: lp_doc.Sent, head_pos):
        # We can only change number of a word
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]
        phrase_words = phrase.get_words(False)

        if head_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):
            if head_obj.number == WordNumber.PLUR:
                form = self._pymorphy_inflect(phrase_words[head_pos], "NOUN", {'plur'})
                if form is not None:
                    phrase_words[head_pos] = form

        if head_obj.pos_tag == PosTag.PROPN:
            phrase_words[head_pos] = phrase_words[head_pos].capitalize()

    def inflect_pair(self, phrase: Phrase, sent: lp_doc.Sent, head_pos, mod_pos):
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]
        mod_sent_pos = phrase.get_sent_pos_list()[mod_pos]
        mod_obj = sent[mod_sent_pos]

        phrase_words = phrase.get_words(False)
        form = None
        if head_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):

            if (
                mod_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN)
                and mod_obj.synt_link == SyntLink.NMOD
            ):
                number = 'plur' if mod_obj.number == WordNumber.PLUR else 'sing'
                form = self._pymorphy_inflect(phrase_words[mod_pos], "NOUN", {number, 'gent'})
                if form is not None and mod_obj.pos_tag == PosTag.PROPN:
                    form = form.capitalize()

                extra = phrase.get_extra()
                extra[mod_pos] = {Attr.CASE: WordCase.GEN}
            elif mod_obj.pos_tag == PosTag.PROPN:
                gender = self._gender2pymorphy(head_obj.gender)
                form = None
                if gender is not None:
                    form = self._pymorphy_inflect(phrase_words[mod_pos], "NOUN", {gender})

                if form is None:
                    form = phrase_words[mod_pos]

                form = form.capitalize()
            elif mod_obj.pos_tag in (PosTag.ADJ, PosTag.PARTICIPLE):

                feats = set()
                number = 'plur' if head_obj.number == WordNumber.PLUR else 'sing'
                feats.add(number)
                if number != 'plur':
                    gender = self._gender2pymorphy(head_obj.gender)
                    if gender is not None:
                        feats.add(gender)

                case = 'nomn'
                extra = phrase.get_extra()[head_pos]
                if extra is not None:
                    case = extra.get(Attr.CASE, WordCase.NOM)
                    if case == WordCase.NOM:
                        case = 'nomn'
                    elif case == WordCase.GEN:
                        case = 'gent'
                    else:
                        raise RuntimeError(f"Unsupported case {case}")

                feats.add(case)

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

    def _pymorphy_inflect(self, word: str, tag: str, feats, mod_obj: Optional[WordObj] = None):
        # ru_inflector = _get_ru_inflector()
        results = self._pymorphy.parse(word)

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
            inflected = parsed.inflect(feats)

            if inflected is not None:
                return inflected.word

        return None


EN_INFLECTOR = None


def _get_en_inflector():
    global EN_INFLECTOR
    if EN_INFLECTOR is None:
        EN_INFLECTOR = EnInflector()
    return EN_INFLECTOR


class EnInflector(Inflector):
    def __init__(self):
        p = importlib.resources.files('pylp.phrases.data').joinpath('en_lemma_exc.json.gz')
        with p.open('rb') as bf:
            gf = gzip.GzipFile(fileobj=bf)
            excep_dict = json.load(
                gf, object_hook=lambda d: d if 'pap' not in d else VerbExcpForms.from_json(d)
            )

        self._noun_excep_dict: Mapping[str, str] = excep_dict['noun']
        self._verb_excep_dict: Mapping[str, VerbExcpForms] = excep_dict['verb']

    def _inflect_plural(self, lemma: str) -> Optional[str]:
        if not lemma:
            return None
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

        phrase_words = phrase.get_words(False)
        if head_obj.number == WordNumber.PLUR:
            form = self._inflect_plural(phrase_words[head_pos])
            if form is not None:
                phrase_words[head_pos] = form

        if head_obj.pos_tag == PosTag.PROPN:
            phrase_words[head_pos] = phrase_words[head_pos].capitalize()

    def inflect_pair(self, phrase: Phrase, sent: lp_doc.Sent, head_pos, mod_pos):
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]
        mod_sent_pos = phrase.get_sent_pos_list()[mod_pos]
        mod_obj = sent[mod_sent_pos]

        phrase_words = phrase.get_words(False)
        current_lemma = phrase_words[mod_pos]
        form = None
        if head_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):

            if mod_obj.pos_tag in (PosTag.NOUN, PosTag.PROPN):
                if mod_obj.number == WordNumber.PLUR:
                    form = self._inflect_plural(current_lemma)
                if mod_obj.pos_tag == PosTag.PROPN:
                    if form is None:
                        form = current_lemma
                    form = form.capitalize()

            elif (
                mod_obj.pos_tag == PosTag.PARTICIPLE and mod_obj.tense in (None, WordTense.PRES)
            ) or mod_obj.pos_tag == PosTag.PARTICIPLE_ADVERB:
                # The second condition is a legacy of erroneous convertation from UD
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
                    else:
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
                    else:
                        form = current_lemma + 'ed'

        if form is not None:
            phrase_words[mod_pos] = form
