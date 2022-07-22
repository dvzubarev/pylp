#!/usr/bin/env python3

import hashlib
import logging
from typing import Any, overload, Optional, Iterator, List, Tuple, Dict


from pylp import common

from pylp.word_obj import WordObj
from pylp.phrases.phrase import Phrase
from pylp.utils import adjust_syntax_links


class Sent:
    def __init__(
        self,
        words: List[WordObj] = None,
        phrases: List[Phrase] = None,
        bounds: Tuple[int, int] = None,
    ) -> None:
        self._words: List[WordObj] = []
        if words is not None:
            self._words = words

        self._phrases: List[Phrase] = []
        if phrases:
            self._phrases = phrases

        self.bounds: Optional[Tuple[int, int]] = None
        if bounds:
            self.bounds = bounds

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

    def __getitem__(self, item: slice | int) -> List[WordObj] | WordObj:
        return self._words[item]

    def to_dict(self):
        words = []
        d: Dict[str, Any] = {'words': words}
        for w in self._words:
            words.append(w.to_dict())

        if self.bounds is not None:
            d['bounds'] = self.bounds

        if self._phrases:
            phrases = []
            d['phrases'] = phrases
            for p in self._phrases:
                phrases.append(p.to_dict())

        return d

    @classmethod
    def from_dict(cls, dic):
        words = []
        for wdic in dic['words']:
            words.append(WordObj.from_dict(wdic))
        phrases = []
        if 'phrases' in dic:
            for pdic in dic['phrases']:
                phrases.append(Phrase.from_dict(pdic))

        bounds = dic.get('bounds')
        return cls(words, phrases, bounds)

    def __str__(self) -> str:
        s = ''
        if self.bounds:
            s = f"Offset: {self.bounds[0]}, len: {self.bounds[1]}, "

        s += 'Words:\n'
        words_s = []
        for i, w in enumerate(self._words):
            words_s.append(f"Word #{i}: {w}\n")

        phrases_s = []
        if self._phrases:
            phrases_s.append('Phrases:\n')
            for p in self._phrases:
                phrases_s.append(str(p))
                phrases_s.append('\n')

        return ''.join([s] + words_s + phrases_s)


FragmentType = List[Tuple[int, int]]


class Doc:
    def __init__(
        self,
        doc_id: str,
        text: str = None,
        sents: Optional[List[Sent]] = None,
        lang: Optional[str | common.Lang] = None,
    ) -> None:

        self.doc_id = doc_id

        self._text = None
        self._text_hash = None
        if text is not None:
            self.text = text

        self._sents: List[Sent] = []
        if sents is not None:
            self._sents = sents

        self._lang: Optional[common.Lang] = None
        if lang is not None:
            self.lang = lang
        self._fragments: Dict[str, FragmentType] = {}

        self._ling_meta = {'model': {}, 'properties': [], 'post_processors': {'kinds': []}}

    @property
    def text(self) -> Optional[str]:
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        m = hashlib.sha1()
        m.update(text.encode('utf8'))
        self._text_hash = m.hexdigest()

    @property
    def text_hash(self) -> Optional[str]:
        return self._text_hash

    @property
    def lang(self) -> Optional[common.Lang]:
        return self._lang

    @lang.setter
    def lang(self, lang: common.Lang | str):
        if isinstance(lang, str):
            self._lang = common.LANG_DICT.get(lang.upper(), common.Lang.UNDEF)
        else:
            self._lang = lang

    def set_fragments(self, fragments: FragmentType, name='default'):
        self._fragments[name] = fragments

    def get_fragments(self, name='default'):
        return self._fragments.get(name)

    def get_all_fragments(self):
        return self._fragments

    def add_sent(self, sent_obj: Sent):
        self._sents.append(sent_obj)

    def sents(self) -> Iterator[Sent]:
        for s in self._sents:
            yield s

    def update_ling_model_info(self, **kwargs):
        self._ling_meta['model'].update(kwargs)

    def update_post_processors_info(self, **kwargs):
        self._ling_meta['post_processors'].update(kwargs)

    def add_ling_prop(self, val):
        self._ling_meta['properties'].append(val)

    def get_ling_meta(self):
        return self._ling_meta

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

    def __getitem__(self, item: slice | int) -> List[Sent] | Sent:
        return self._sents[item]

    def __repr__(self):
        s = f"<Doc: {self.doc_id}; "
        if self.text is not None:
            text_s = f"text len: {len(self.text)}, text hash: {self._text_hash}; "
        else:
            text_s = ''
        if self._sents:
            sents_s = f"sents: {len(self._sents)}; "
        else:
            sents_s = ''

        return ''.join([s, text_s, sents_s, '>'])

    def to_dict(self):
        d = {'id': self.doc_id, 'ling_meta': self._ling_meta}
        if self._fragments:
            d['fragments'] = self._fragments

        if self._text is not None:
            d['text'] = self._text
        if self._text_hash is not None:
            d['text_hash'] = self._text_hash

        if self._lang is not None:
            d['lang'] = self._lang

        sents = []
        d['sents'] = sents
        for sent in self._sents:
            sents.append(sent.to_dict())
        return d

    @classmethod
    def from_dict(cls, dic):
        doc = cls(dic['id'], lang=dic.get('lang'))
        text = None
        text_hash = None
        if 'text' in dic:
            text = dic['text']
        if 'text_hash' in dic:
            text_hash = dic['text_hash']
        doc._text = text
        doc._text_hash = text_hash
        if 'fragments' in dic:
            doc._fragments = dic['fragments']
        if 'ling_meta' in dic:
            doc._ling_meta = dic['ling_meta']

        for sdic in dic['sents']:
            doc.add_sent(Sent.from_dict(sdic))
        return doc

    def __str__(self) -> str:
        s = f"Doc: {self.doc_id}; "
        if self.lang is not None:
            s += f"lang: {self.lang}; "

        if self.text is not None:
            text_s = f"text len: {len(self.text)}, text hash: {self._text_hash}; "
        else:
            text_s = ''

        sents_s = []
        if self._sents:
            sents_s = [f"sents: {len(self._sents)}\n"]
            for i, sent in enumerate(self._sents):
                sents_s.append(f"Sent #{i}: {sent}")

        fragments_s = []
        if self._fragments:
            fragments_s = ["Fragments:\n"]
            for name, frag in self._fragments.items():
                fragments_s.append(f"{name}: {frag}\n")

        return ''.join([s, text_s] + sents_s + fragments_s + ['\n', str(self._ling_meta)])
