#!/usr/bin/env python3

import copy
from typing import List, Optional, Tuple
from enum import IntEnum

import libpyexbase
import pylp.common as lp
from pylp.word_obj import WordObj
from pylp.utils import word_id_combiner


class PhraseId:
    def __init__(self, word_obj: Optional[WordObj] = None):

        self._prep_id = None
        self._id: int = 0
        self._root = None
        self._id_parts = []

        if word_obj is not None:
            word_id = word_obj.word_id
            if word_id is None:
                raise RuntimeError(f"Unable to calculate word id for a word: {word_obj}")
            self._id = word_id
            self._root = word_id
            self._id_parts = [word_id]
            extra = word_obj.extra
            if lp.Attr.PREP_WHITE_LIST in extra:
                _, _, prep_id = extra[lp.Attr.PREP_WHITE_LIST]
                self._prep_id = prep_id

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__['_id'] = self._id
        result.__dict__['_root'] = self._root
        result.__dict__['_id_parts'] = copy.copy(self._id_parts)
        result.__dict__['_prep_id'] = self._prep_id
        return result

    def get_id(self, with_prep=False):
        if with_prep and self._prep_id:
            return libpyexbase.combine_word_id(self._prep_id, self._id)
        return self._id

    def merge_mod(self, mod: "PhraseId", on_left):
        if self._root is None:
            raise RuntimeError("Can't merge root is not initialized!")
        mod_id = mod.get_id(with_prep=True)
        if on_left:
            i = 0
            while self._id_parts[i] != self._root and mod_id > self._id_parts[i]:
                i += 1
        else:
            i = len(self._id_parts)
            while self._id_parts[i - 1] != self._root and mod_id < self._id_parts[i - 1]:
                i -= 1
        self._id_parts.insert(i, mod_id)
        self._id = word_id_combiner(self._id_parts)
        return self

    def to_dict(self):
        d = {'id': self._id}
        if self._prep_id is not None:
            d['prep_id'] = self._prep_id
        return d

    @classmethod
    def from_dict(cls, dic):
        phrase_id = cls()
        phrase_id._prep_id = dic.get('prep_id')
        phrase_id._id = dic['id']
        return phrase_id

    def __str__(self):
        return self._id


class HeadModifier:
    def __init__(
        self, prep_modifier: Tuple | None = None, repr_mod_suffix: str | None = None
    ) -> None:
        self.prep_modifier = prep_modifier
        self.repr_mod_suffix = repr_mod_suffix

    def to_dict(self, use_shorthand_keys: bool = False):
        if self.prep_modifier is None and self.repr_mod_suffix is None:
            return {}
        return {
            'p' if use_shorthand_keys else 'prep_mod': self.prep_modifier,
            'r' if use_shorthand_keys else 'repr_mod_suffix': self.repr_mod_suffix,
        }

    @classmethod
    def from_dict(cls, dic):
        hm = cls()
        use_shorthand_keys = 'prep_mod' in dic
        hm.prep_modifier = dic.get('p' if use_shorthand_keys else 'prep_mod')
        hm.repr_mod_suffix = dic.get('r' if use_shorthand_keys else 'repr_mod_suffix')


class ReprEnhType(IntEnum):
    ADD_WORD = 0
    ADD_SUFFIX = 1


class ReprEnhancer:
    def __init__(self, rel_pos: int, enh_type: ReprEnhType, value: str) -> None:
        self.rel_pos = rel_pos
        self.enh_type = enh_type
        self.value = value

    def to_dict(self, use_shorthand_keys: bool = False):
        return {
            'p' if use_shorthand_keys else 'rel_pos': self.rel_pos,
            'e' if use_shorthand_keys else 'enh_type': self.enh_type,
            'v' if use_shorthand_keys else 'value': self.value,
        }

    @classmethod
    def from_dict(cls, dic):
        use_shorthand_keys = 'rel_pos' not in dic
        return cls(
            dic['p' if use_shorthand_keys else 'rel_pos'],
            dic['e' if use_shorthand_keys else 'enh_type'],
            dic['v' if use_shorthand_keys else 'value'],
        )


class PhraseType(IntEnum):
    DEFAULT = 0
    MWE = 1


class Phrase:
    def __init__(
        self,
        size: int = 0,
        head_pos: int = 0,
        sent_pos_list: List[int] | None = None,
        words: List[str] | None = None,
        deps: List[int] | None = None,
        id_holder: PhraseId | None = None,
        head_modifier: HeadModifier | None = None,
        repr_modifiers: List[List[ReprEnhancer] | None] | None = None,
    ):
        self._size = size
        self._head_pos = head_pos
        self._sent_pos_list = sent_pos_list if sent_pos_list is not None else []
        if self._size == 0:
            self._size = len(self._sent_pos_list)
        self._words = words if words is not None else []
        self._deps = deps if deps is not None else []
        self._id_holder = id_holder if id_holder is not None else PhraseId()
        # cosmetic modifiers
        self._head_modifier = head_modifier if head_modifier is not None else HeadModifier()
        self._repr_modifiers = repr_modifiers if repr_modifiers is not None else []
        self.phrase_type = PhraseType.DEFAULT

    @classmethod
    def from_word(cls: type["Phrase"], pos: int, word_obj: WordObj):
        if word_obj.lemma is None:
            raise RuntimeError("Unindentified word")

        prep_mod = word_obj.extra.get(lp.Attr.PREP_WHITE_LIST)
        repr_mod_suffix = word_obj.extra.get(lp.Attr.REPR_MOD_SUFFIX)
        return cls(
            size=1,
            head_pos=0,
            sent_pos_list=[pos],
            words=[word_obj.lemma],
            deps=[0],
            id_holder=PhraseId(word_obj),
            head_modifier=HeadModifier(prep_modifier=prep_mod, repr_mod_suffix=repr_mod_suffix),
            repr_modifiers=[None],
        )

    def size(self):
        return self._size

    def get_head_modifier(self) -> None | HeadModifier:
        """Get cosmetic head modifiers. This modifiers are used when producing
        string for a phrase."""
        return self._head_modifier

    def get_head_pos(self):
        """Relative position of the head in the phrase."""
        return self._head_pos

    def sent_hp(self):
        """Position of the head in the sentence."""
        return self._sent_pos_list[self._head_pos]

    def set_sent_pos_list(self, sent_pos_list):
        self._sent_pos_list = sent_pos_list

    def get_sent_pos_list(self):
        """Positions of phrase parts in the sentence."""
        return self._sent_pos_list

    def get_words(self):
        return self._words

    def get_str_repr(self):
        if not any(m for m in self._repr_modifiers):
            return ' '.join(self._words)

        words = copy.copy(self._words)

        for pos, repr_enh_list in enumerate(self._repr_modifiers):
            if repr_enh_list is None:
                continue
            for repr_enh in repr_enh_list:
                match repr_enh.enh_type:
                    case ReprEnhType.ADD_WORD:
                        modify_pos = pos + repr_enh.rel_pos
                        words[modify_pos] = f'{repr_enh.value} ' + words[modify_pos]
                    case ReprEnhType.ADD_SUFFIX:
                        modify_pos = pos + repr_enh.rel_pos
                        words[modify_pos] += repr_enh.value

        return ' '.join(words)

    def get_deps(self):
        """Relative offsets from a word to its head word. The word with 0 value is the root."""
        return self._deps

    def get_repr_modifiers(self):
        return self._repr_modifiers

    def get_id_holder(self):
        return self._id_holder

    def get_id(self):
        return self._id_holder.get_id()

    def intersects(self, other: "Phrase"):
        other_pos_list = other.get_sent_pos_list()
        return not (
            self._sent_pos_list[-1] < other_pos_list[0]
            or self._sent_pos_list[0] > other_pos_list[-1]
        )

    def overlaps(self, other: "Phrase"):
        other_pos_list = other.get_sent_pos_list()
        return (
            self._sent_pos_list[0] <= other_pos_list[0]
            and self._sent_pos_list[-1] >= other_pos_list[-1]
        )

    def contains(self, other: "Phrase"):
        if not self.overlaps(other):
            return False
        other_pos_list = other.get_sent_pos_list()
        i = j = 0
        while i < len(other_pos_list):
            if other_pos_list[i] < self._sent_pos_list[j]:
                return False
            if other_pos_list[i] == self._sent_pos_list[j]:
                j += 1
                i += 1
            else:
                j += 1
        return True

    def to_dict(self, use_shorthand_keys: bool = False):
        d = {
            'h' if use_shorthand_keys else 'head_pos': self._head_pos,
            'p' if use_shorthand_keys else 'sent_pos_list': self._sent_pos_list,
            'w' if use_shorthand_keys else 'words': self._words,
            'd' if use_shorthand_keys else 'deps': self._deps,
            'i' if use_shorthand_keys else 'id_holder': self._id_holder.to_dict(),
        }
        if hdd := self._head_modifier.to_dict(use_shorthand_keys=use_shorthand_keys):
            d['hm' if use_shorthand_keys else 'head_mod'] = hdd

        if self._repr_modifiers:
            if any(m is not None for m in self._repr_modifiers):
                repr_modifiers = [
                    (
                        [m.to_dict(use_shorthand_keys=use_shorthand_keys) for m in mod_list]
                        if mod_list is not None
                        else None
                    )
                    for mod_list in self._repr_modifiers
                ]
                d['r' if use_shorthand_keys else 'repr_modifiers'] = repr_modifiers

        if self.phrase_type != PhraseType.DEFAULT:
            d['t' if use_shorthand_keys else 'type'] = self.phrase_type
        return d

    @classmethod
    def from_dict(cls, dic):
        use_shorthand_keys = 'id_holder' not in dic and 'i' in dic
        phrase = cls()
        phrase._head_pos = dic.get('h' if use_shorthand_keys else 'head_pos', 0)
        phrase._sent_pos_list = dic.get('p' if use_shorthand_keys else 'sent_pos_list', [])
        phrase._words = dic.get('w' if use_shorthand_keys else 'words', [])
        phrase._deps = dic.get('d' if use_shorthand_keys else 'deps', [])
        phrase._head_modifier = HeadModifier.from_dict(
            dic.get('hm' if use_shorthand_keys else 'head_mod', {})
        )
        phrase._repr_modifiers = [
            [ReprEnhancer.from_dict(d) for d in mod_list] if mod_list is not None else None
            for mod_list in dic.get('r' if use_shorthand_keys else 'repr_modifiers', [])
        ]
        if not phrase._repr_modifiers:
            phrase._repr_modifiers = [None] * len(phrase._sent_pos_list)
        phrase._id_holder = PhraseId.from_dict(dic['i' if use_shorthand_keys else 'id_holder'])
        phrase.phrase_type = dic.get('t' if use_shorthand_keys else 'type', PhraseType.DEFAULT)

        phrase._size = len(phrase._sent_pos_list)
        return phrase

    def __repr__(self) -> str:
        return f"Phrase(id={self.get_id()}, words={self.get_words()})"

    def __str__(self):
        return f"Id:{self.get_id()}, str_repr: {self.get_str_repr()}, positions: {self.get_sent_pos_list()}"
