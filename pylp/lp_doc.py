#!/usr/bin/env python3

from typing import overload, Optional, Union, Iterator, List, Tuple, Dict

from pylp import common


class WordObj:
    __slots__ = (
        # '_pos',
        'lemma',
        'form',
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
    )

    def __init__(
        self,
        *,
        lemma='',
        form='',
        pos_tag=common.PosTag.UNDEF,
        parent_offs=None,
        synt_link=None,
        lang=None,
        number=None,
        gender=None,
    ) -> None:
        # basic info
        self.lemma: str = lemma
        self.form: str = form
        self.offset: int = -1
        self.len: int = 0  # len of form
        self.pos_tag: common.PosTag = pos_tag
        self.parent_offs: Optional[int] = parent_offs
        self.synt_link: Optional[common.SyntLink] = synt_link

        self.lang: Optional[common.Lang] = lang

        # morph features
        self.number: Optional[common.WordNumber] = number
        self.gender: Optional[common.WordGender] = gender
        self.case: Optional[common.WordCase] = None
        self.tense: Optional[common.WordTense] = None
        self.person: Optional[common.WordPerson] = None
        self.comp: Optional[common.WordComparison] = None
        self.aspect: Optional[common.WordAspect] = None
        self.voice: Optional[common.WordVoice] = None
        self.animacy: Optional[common.WordAnimacy] = None


class Sent:
    def __init__(self) -> None:
        self._words: List[WordObj] = []

    def add_word(self, word_obj: WordObj):
        self._words.append(word_obj)

    def words(self) -> Iterator[WordObj]:
        for w in self._words:
            yield w

    def set_words(self, new_words: List[WordObj]):
        self._words = new_words

    def __len__(self) -> int:
        return len(self._words)

    def __iter__(self) -> Iterator[WordObj]:
        yield from self._words

    @overload
    def __getitem__(self, item: slice) -> List[WordObj]:
        ...

    @overload
    def __getitem__(self, item: int) -> WordObj:
        ...

    def __getitem__(self, item: Union[slice, int]) -> Union[List[WordObj], WordObj]:
        return self._words[item]


FragmentType = List[Tuple[int, int]]


class Doc:
    def __init__(self, lang: Optional[str | common.Lang] = None) -> None:
        self._sents: List[Sent] = []
        self._lang: Optional[common.Lang] = None
        if lang is not None:
            self.lang = lang
        self._fragments: Dict[str, FragmentType] = {}

    @property
    def lang(self) -> Optional[common.Lang]:
        return self._lang

    @lang.setter
    def lang(self, lang: Union[common.Lang, str]):
        if isinstance(lang, str):
            self._lang = common.LANG_DICT.get(lang.upper(), common.Lang.UNDEF)
        else:
            self._lang = lang

    def set_fragments(self, fragments: FragmentType, name='default'):
        self._fragments[name] = fragments

    def get_fragments(self, name='default'):
        return self._fragments.get(name)

    def add_sent(self, sent_obj: Sent):
        self._sents.append(sent_obj)

    def sents(self) -> Iterator[Sent]:
        for s in self._sents:
            yield s

    def __len__(self) -> int:
        return len(self._sents)

    def __iter__(self) -> Iterator[Sent]:
        yield from self._sents

    @overload
    def __getitem__(self, item: slice) -> List[Sent]:
        ...

    @overload
    def __getitem__(self, item: int) -> Sent:
        ...

    def __getitem__(self, item: Union[slice, int]) -> Union[List[Sent], Sent]:
        return self._sents[item]

    def __repr__(self):
        return f"<Doc: {len(self._sents)} sents>"
