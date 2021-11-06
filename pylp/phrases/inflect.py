#!/usr/bin/env python
# coding: utf-8

from typing import List

import pymorphy2

from pylp.common import Attr, Lang, PosTag, WordGender, WordVoice, WordTense, WordCase
from pylp.phrases.builder import Phrase


# Abstract classes
class Inflector:
    def inflect_head(self, phrase: Phrase, sent: List[dict], head_pos):
        raise NotImplementedError("inflect head is not implemented")

    def inflect_pair(self, phrase: Phrase, sent: List[dict], head_pos, mod_pos):
        raise NotImplementedError("inflect pair is not implemented")


# API


def inflect_phrases(phrases: List[Phrase], sent: List[dict], text_lang):
    for phrase in phrases:
        inflect_phrase(phrase, sent, text_lang)


def inflect_phrase(phrase: Phrase, sent: List[dict], text_lang):
    if any(sent[i].get(Attr.LANG, text_lang) == Lang.RU for i in phrase.get_sent_pos_list()):
        return inflect_ru_phrase(phrase, sent)
    return inflect_en_phrase(phrase, sent)


def inflect_ru_phrase(phrase: Phrase, sent: List[dict]):
    _inflect_mods_of_head(phrase, sent, phrase.get_head_pos(), inflector=_get_ru_inflector())


def inflect_en_phrase(phrase: Phrase, sent: List[dict]):
    # raise NotImplementedError("en inflecting does not implemented yet!")
    pass


# Implementation


def _inflect_mods_of_head(
    phrase: Phrase,
    sent: List[dict],
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
        if not inflected[mod_pos] and l is not None and mod_pos + l == head_pos:
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

    def inflect_head(self, phrase: Phrase, sent: List[dict], head_pos):
        # We can only change number of a word
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]

        if head_obj[Attr.POS_TAG] == PosTag.NOUN:
            if Attr.PLURAL not in head_obj:
                return

            phrase_words = phrase.get_words(False)
            form = self._pymorphy_inflect(phrase_words[head_pos], "NOUN", {'plur'})
            if form is not None:
                phrase_words[head_pos] = form

    def inflect_pair(self, phrase: Phrase, sent: List[dict], head_pos, mod_pos):
        head_sent_pos = phrase.get_sent_pos_list()[head_pos]
        head_obj = sent[head_sent_pos]
        mod_sent_pos = phrase.get_sent_pos_list()[mod_pos]
        mod_obj = sent[mod_sent_pos]

        phrase_words = phrase.get_words(False)
        form = None
        if head_obj[Attr.POS_TAG] == PosTag.NOUN:
            if mod_obj[Attr.POS_TAG] == PosTag.NOUN:
                number = 'plur' if Attr.PLURAL in mod_obj else 'sing'
                form = self._pymorphy_inflect(phrase_words[mod_pos], "NOUN", {number, 'gent'})
                extra = phrase.get_extra()
                extra[mod_pos] = {Attr.CASE: WordCase.GEN}
            elif mod_obj[Attr.POS_TAG] in (PosTag.ADJ, PosTag.PARTICIPLE):

                feats = set()
                number = 'plur' if Attr.PLURAL in head_obj else 'sing'
                feats.add(number)
                if number != 'plur':
                    gender = self._gender2pymorphy(head_obj.get(Attr.GENDER))
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

                if mod_obj[Attr.POS_TAG] == PosTag.ADJ:
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

    def _pymorphy_find_participle(self, inf, mod_obj):
        if mod_obj is None:
            return None

        voice = mod_obj.get(Attr.VOICE, WordVoice.ACT)
        tense = mod_obj.get(Attr.TENSE)
        if voice is None or tense is None:
            return None

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
            if l.tag.POS == 'PRTF' and l.tag.voice == voice and l.tag.tense == tense:
                return l
        return None

    def _pymorphy_inflect(self, word, tag, feats, mod_obj=None):
        # ru_inflector = _get_ru_inflector()
        results = self._pymorphy.parse(word)

        parsed = None

        if tag == "PRTF":
            parsed = self._pymorphy_find_participle(results[0], mod_obj)
        else:
            for res in results:
                if res.tag.POS == tag:
                    parsed = res
                    break

        if parsed is not None:
            return parsed.inflect(feats).word
        return None
