#!/usr/bin/env python3

from typing import overload, Optional, Union, Iterator, List, Tuple, Dict


from pylp import common

from pylp.word_obj import WordObj
from pylp.phrases.phrase import Phrase


class Sent:
    def __init__(
        self, words: Optional[List[WordObj]] = None, phrases: Optional[list[Phrase]] = None
    ) -> None:
        self._words: List[WordObj] = []
        if words is not None:
            self._words = words

        self._phrases: List[Phrase] = []
        if phrases:
            self._phrases = phrases

    def add_word(self, word_obj: WordObj):
        self._words.append(word_obj)

    def words(self) -> Iterator[WordObj]:
        for w in self._words:
            yield w

    def set_words(self, new_words: List[WordObj]):
        self._words = new_words

    def phrases(self) -> Iterator[Phrase]:
        yield from self._phrases

    def set_phrases(self, phrases):
        self._phrases = phrases

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
    def __init__(
        self, sents: Optional[List[Sent]] = None, lang: Optional[str | common.Lang] = None
    ) -> None:
        self._sents: List[Sent] = []
        if sents is not None:
            self._sents = sents

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
