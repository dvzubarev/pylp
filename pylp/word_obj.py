#!/usr/bin/env python3

from __future__ import annotations

from typing import Dict, Optional

import libpyexbase

from pylp import common
from pylp.common import Attr


class WordObj:
    __slots__ = (
        # '_pos',
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
        'comp',
        'aspect',
        'voice',
        'animacy',
        'extra',
    )

    def __init__(
        self,
        *,
        pos_tag=common.PosTag.UNDEF,
        lemma=None,
        form=None,
        parent_offs=None,
        synt_link=None,
        lang=None,
        number=None,
        gender=None,
        tense=None,
        case=None,
        voice=None,
    ) -> None:
        # basic info
        self.pos_tag: common.PosTag = pos_tag

        self.lemma: Optional[str] = lemma
        self.form: Optional[str] = form
        self._word_id: Optional[int] = None

        # token in the original text
        self.offset: Optional[int] = None
        self.len: Optional[int] = None  # len of form

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
        self.person: Optional[common.WordPerson] = None
        self.comp: Optional[common.WordComparison] = None
        self.aspect: Optional[common.WordAspect] = None
        self.voice: Optional[common.WordVoice] = voice
        self.animacy: Optional[common.WordAnimacy] = None

        self.extra: dict = {}

    @property
    def word_id(self) -> Optional[int]:
        if self._word_id is None:
            if not self.lemma:
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
        if self.word_id is not None:
            d[Attr.WORD_ID] = self.word_id
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
        if self.comp is not None:
            d[Attr.COMPARISON] = self.comp
        if self.aspect is not None:
            d[Attr.ASPECT] = self.aspect
        if self.voice is not None:
            d[Attr.VOICE] = self.voice
        if self.animacy is not None:
            d[Attr.ANIMACY] = self.animacy
        return d

    @classmethod
    def from_dict(cls, dic):
        word_obj = cls()
        for key, value in dic.items():
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
                    word_obj.synt_link = value
                case Attr.LANG:
                    word_obj.lang = value
                case Attr.NUMBER:
                    word_obj.number = value
                case Attr.GENDER:
                    word_obj.gender = value
                case Attr.CASE:
                    word_obj.case = value
                case Attr.TENSE:
                    word_obj.tense = value
                case Attr.PERSON:
                    word_obj.person = value
                case Attr.COMPARISON:
                    word_obj.comp = value
                case Attr.ASPECT:
                    word_obj.aspect = value
                case Attr.VOICE:
                    word_obj.voice = value
                case Attr.ANIMACY:
                    word_obj.animacy = value
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
        if self.comp is not None:
            parts_s.append(f"comp: {es(self.comp)}, ")
        if self.aspect is not None:
            parts_s.append(f"aspect: {es(self.aspect)}, ")
        if self.voice is not None:
            parts_s.append(f"voice: {es(self.voice)}, ")
        if self.animacy is not None:
            parts_s.append(f"animacy: {es(self.animacy)}, ")
        parts_s[-1] = parts_s[-1][:-2]
        return ''.join(parts_s)
