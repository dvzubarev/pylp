#!/usr/bin/env python3

from __future__ import annotations

from typing import Dict, Optional, Any

import libpyexbase

from pylp import common
from pylp.common import Attr


class WordObj:
    __slots__ = (
        'lemma',
        'form',
        '_word_id',
        'offset',
        'len',
        'pos_tag',
        'parent_offs',
        'synt_link',
        'lang',
        'number',
        'gender',
        'case',
        'tense',
        'person',
        'degree',
        'aspect',
        'voice',
        'mood',
        'num_type',
        'animacy',
        'extra',
        'mwes',
    )

    def __init__(
        self,
        *,
        pos_tag: common.PosTag = common.PosTag.UNDEF,
        lemma: str | None = None,
        form: str | None = None,
        offset: int | None = None,
        length: int | None = None,
        parent_offs: int | None = None,
        synt_link: common.SyntLink | None = None,
        lang: common.Lang | None = None,
        number: common.WordNumber | None = None,
        gender: common.WordGender | None = None,
        tense: common.WordTense | None = None,
        person: common.WordPerson | None = None,
        case: common.WordCase | None = None,
        voice: common.WordVoice | None = None,
        degree: common.WordDegree | None = None,
    ) -> None:
        # basic info
        self.pos_tag: common.PosTag = pos_tag

        self.lemma: Optional[str] = lemma
        self.form: Optional[str] = form
        self._word_id: Optional[int] = None

        # token in the original text
        self.offset: Optional[int] = offset
        self.len: Optional[int] = length  # len of a token(form)

        # synt
        self.parent_offs: Optional[int] = parent_offs
        self.synt_link: Optional[common.SyntLink] = synt_link

        # optional word lang
        self.lang: Optional[common.Lang] = lang

        # morph features
        self.number: Optional[common.WordNumber] = number
        self.gender: Optional[common.WordGender] = gender
        self.case: Optional[common.WordCase] = case
        self.tense: Optional[common.WordTense] = tense
        self.person: Optional[common.WordPerson] = person
        self.degree: Optional[common.WordDegree] = degree
        self.aspect: Optional[common.WordAspect] = None
        self.voice: Optional[common.WordVoice] = voice
        self.mood: Optional[common.WordMood] = None
        self.num_type: Optional[common.WordNumType] = None
        self.animacy: Optional[common.WordAnimacy] = None

        self.extra: dict = {}

        # Word can be associated with one or more MWEs.
        # This word is a head in MWE phrases
        # Multipe mwe possible when a word has multiple conjuct modifiers.
        self.mwes: list[Any] = []

    @property
    def word_id(self) -> Optional[int]:
        if self._word_id is None:
            if self.lemma is None:
                return None
            if self.lang is None:
                self._word_id = libpyexbase.detect_lang_calc_word_id(self.lemma, True)
            else:
                self._word_id = libpyexbase.calc_word_id(self.lemma, self.lang, True)
        return self._word_id

    @word_id.setter
    def word_id(self, wid: int):
        self._word_id = wid

    def to_dict(self) -> Dict[str, int | str]:
        d: Dict[str, int | str] = {Attr.POS_TAG: self.pos_tag}
        if self.lemma is not None:
            d[Attr.WORD_LEMMA] = self.lemma
        if self.form is not None:
            d[Attr.WORD_FORM] = self.form
        if self._word_id is not None:
            d[Attr.WORD_ID] = self._word_id
        if self.offset is not None:
            d[Attr.OFFSET] = self.offset
        if self.len is not None:
            d[Attr.LENGTH] = self.len
        if self.parent_offs is not None:
            d[Attr.SYNTAX_PARENT] = self.parent_offs
        if self.synt_link is not None:
            d[Attr.SYNTAX_LINK_NAME] = self.synt_link
        if self.lang is not None:
            d[Attr.LANG] = self.lang
        if self.number is not None:
            d[Attr.NUMBER] = self.number
        if self.gender is not None:
            d[Attr.GENDER] = self.gender
        if self.case is not None:
            d[Attr.CASE] = self.case
        if self.tense is not None:
            d[Attr.TENSE] = self.tense
        if self.person is not None:
            d[Attr.PERSON] = self.person
        if self.degree is not None:
            d[Attr.DEGREE] = self.degree
        if self.aspect is not None:
            d[Attr.ASPECT] = self.aspect
        if self.voice is not None:
            d[Attr.VOICE] = self.voice
        if self.mood is not None:
            d[Attr.MOOD] = self.mood
        if self.num_type is not None:
            d[Attr.NUM_TYPE] = self.num_type
        if self.animacy is not None:
            d[Attr.ANIMACY] = self.animacy
        return d

    @classmethod
    def from_dict(cls, dic):
        word_obj = cls()
        for key, value in dic.items():
            if value is None:
                continue
            match key:
                case Attr.POS_TAG:
                    word_obj.pos_tag = common.PosTag(value)
                case Attr.WORD_LEMMA:
                    word_obj.lemma = value
                case Attr.WORD_FORM:
                    word_obj.form = value
                case Attr.WORD_ID:
                    word_obj.word_id = value
                case Attr.OFFSET:
                    word_obj.offset = value
                case Attr.LENGTH:
                    word_obj.len = value
                case Attr.SYNTAX_PARENT:
                    word_obj.parent_offs = value
                case Attr.SYNTAX_LINK_NAME:
                    word_obj.synt_link = common.SyntLink(value)
                case Attr.LANG:
                    word_obj.lang = common.Lang(value)
                case Attr.NUMBER:
                    word_obj.number = common.WordNumber(value)
                case Attr.GENDER:
                    word_obj.gender = common.WordGender(value)
                case Attr.CASE:
                    word_obj.case = common.WordCase(value)
                case Attr.TENSE:
                    word_obj.tense = common.WordTense(value)
                case Attr.PERSON:
                    word_obj.person = common.WordPerson(value)
                case Attr.DEGREE:
                    word_obj.degree = common.WordDegree(value)
                case Attr.ASPECT:
                    word_obj.aspect = common.WordAspect(value)
                case Attr.VOICE:
                    word_obj.voice = common.WordVoice(value)
                case Attr.MOOD:
                    word_obj.mood = common.WordMood(value)
                case Attr.NUM_TYPE:
                    word_obj.num_type = common.WordNumType(value)
                case Attr.ANIMACY:
                    word_obj.animacy = common.WordAnimacy(value)
        return word_obj

    def __str__(self) -> str:
        es = common.enum2str
        parts_s = [f"PoS: {es(self.pos_tag)}, "]
        if self.lemma is not None:
            parts_s.append(f"lemma: {self.lemma}, ")
        if self.form is not None:
            parts_s.append(f"form: {self.form}, ")
        if self.word_id is not None:
            parts_s.append(f"word_id: {self.word_id:x}, ")
        if self.offset is not None:
            parts_s.append(f"offs: {self.offset}, ")
        if self.len is not None:
            parts_s.append(f"len: {self.len}, ")
        if self.parent_offs is not None:
            parts_s.append(f"parent_offs: {self.parent_offs}, ")
        if self.synt_link is not None:
            parts_s.append(f"synt_link: {es(self.synt_link)}, ")
        if self.lang is not None:
            parts_s.append(f"lang: {es(self.lang)}, ")
        if self.number is not None:
            parts_s.append(f"number: {es(self.number)}, ")
        if self.gender is not None:
            parts_s.append(f"gender: {es(self.gender)}, ")
        if self.case is not None:
            parts_s.append(f"case: {es(self.case)}, ")
        if self.tense is not None:
            parts_s.append(f"tense: {es(self.tense)}, ")
        if self.person is not None:
            parts_s.append(f"person: {es(self.person)}, ")
        if self.degree is not None:
            parts_s.append(f"degree: {es(self.degree)}, ")
        if self.aspect is not None:
            parts_s.append(f"aspect: {es(self.aspect)}, ")
        if self.voice is not None:
            parts_s.append(f"voice: {es(self.voice)}, ")
        if self.mood is not None:
            parts_s.append(f"mood: {es(self.mood)}, ")
        if self.num_type is not None:
            parts_s.append(f"num_type: {es(self.num_type)}, ")
        if self.animacy is not None:
            parts_s.append(f"animacy: {es(self.animacy)}, ")
        parts_s[-1] = parts_s[-1][:-2]
        return ''.join(parts_s)
