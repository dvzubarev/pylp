#!/usr/bin/env python3

import logging
from typing import overload, Optional, Union, Iterator, List, Tuple, Dict


from pylp import common

from pylp.word_obj import WordObj
from pylp.phrases.phrase import Phrase
from pylp.utils import adjust_syntax_links


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
        if self._words and len(new_words) < len(self._words) and self._phrases:
            logging.warning(
                "New words has length < than old words. It may lead to the misaligning with phrases"
            )

        self._words = new_words

    def phrases(self) -> Iterator[Phrase]:
        yield from self._phrases

    def set_phrases(self, phrases):
        self._phrases = phrases

    def filter_words(self, filter_list):
        new_words = []
        new_positions = []
        cur_pos = 0
        for word_pos, word_obj in enumerate(self._words):
            filtered = False
            for filt in filter_list:
                filtered = filt(word_obj, word_pos, self)
                if filtered:
                    break

            if filtered:
                new_positions.append(-1)
            else:
                new_words.append(word_obj)
                new_positions.append(cur_pos)
                cur_pos += 1

        if len(new_words) < len(new_positions):
            adjust_syntax_links(new_words, new_positions)
            self._adjust_phrases(new_positions)
        self._words = new_words

    def _adjust_phrases(self, new_positions):
        if not self._phrases:
            return

        new_phrases = []
        for phrase in self._phrases:
            if any(1 for p in phrase.get_sent_pos_list() if new_positions[p] == -1):
                continue
            pos_list = [new_positions[p] for p in phrase.get_sent_pos_list()]
            phrase.set_sent_pos_list(pos_list)
            new_phrases.append(phrase)
        self._phrases = new_phrases

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
