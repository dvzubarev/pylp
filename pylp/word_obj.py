#!/usr/bin/env python3

from typing import Optional

import libpyexbase

from pylp import common


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
        self.offset: Optional[int] = -1
        self.len: Optional[int] = 0  # len of form

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
    def word_id(self) -> int:
        if self._word_id is None:
            if not self.lemma:
                raise RuntimeError("lemma is empty; can't calculate word_id")
            if self.lang is None:
                self._word_id = libpyexbase.detect_lang_calc_word_id(self.lemma, True)
            else:
                self._word_id = libpyexbase.calc_word_id(self.lemma, self.lang, True)
        return self._word_id

    @word_id.setter
    def word_id(self, wid: int):
        self._word_id = wid
