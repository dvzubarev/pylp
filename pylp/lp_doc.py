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
        'head_offs',
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

    def __init__(self, lemma='', form='', pos_tag=common.PosTag.UNDEF) -> None:
        # basic info
        self.lemma = lemma
        self.form = form
        self.offset = -1
        self.len = 0  # len of form
        self.pos_tag = pos_tag
        self.head_offs = None
        self.synt_link = None

        self.lang = None

        # morph features
        self.number = None
        self.gender = None
        self.case = None
        self.tense = None
        self.person = None
        self.comp = None
        self.aspect = None
        self.voice = None
        self.animacy = None


class Sent:
    def __init__(self) -> None:
        self._words = []

    def add_word(self, word_obj: WordObj):
        self._words.append(word_obj)

    def words(self) -> Iterator[WordObj]:
        for w in self._words:
            yield w

    def __len__(self) -> int:
        return len(self._words)

    def __iter__(self) -> Iterator[WordObj]:
        yield from self._words

    @overload
    def __getitem__(self, item: slice) -> list[WordObj]:
        ...

    @overload
    def __getitem__(self, item: int) -> WordObj:
        ...

    def __getitem__(self, item: slice | int) -> list[WordObj] | WordObj:
        return self._words[item]


FragmentType = List[Tuple[int, int]]


class Doc:
    def __init__(self) -> None:
        self._sents = []
        self._lang = None
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
    def __getitem__(self, item: slice) -> list[Sent]:
        ...

    @overload
    def __getitem__(self, item: int) -> Sent:
        ...

    def __getitem__(self, item: slice | int) -> list[Sent] | Sent:
        return self._sents[item]

    def __repr__(self):
        return f"<Doc: {len(self._sents)} sents>"
