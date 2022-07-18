#!/usr/bin/env python3

import copy
from typing import List

import libpyexbase
import pylp.common as lp
from pylp.word_obj import WordObj
from pylp.utils import word_id_combiner


class PhraseId:
    def __init__(self, word_obj: WordObj):
        word_id = word_obj.word_id

        self._id = word_id
        self._root = word_id
        self._id_parts = [word_id]
        self._prep_id = None

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

    def __str__(self):
        return self._id

    def get_id(self, with_prep=False):
        if with_prep and self._prep_id:
            return libpyexbase.combine_word_id(self._prep_id, self._id)
        return self._id

    def merge_mod(self, mod: "PhraseId", on_left):
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


class Phrase:
    def __init__(self, pos: int = None, word_obj: WordObj = None):
        if pos is not None and word_obj is not None:
            self._head_pos = 0
            self._sent_pos_list = [pos]
            if word_obj.lemma is None:
                raise RuntimeError("Unindentified word")
            self._words = [word_obj.lemma]

            self._deps: List[int] = [0]
            self._extra = [word_obj.extra]

            self._id_holder = PhraseId(word_obj)

    def size(self):
        return len(self._words)

    def get_head_pos(self):
        return self._head_pos

    def set_head_pos(self, head_pos):
        self._head_pos = head_pos

    def sent_hp(self):
        return self._sent_pos_list[self._head_pos]

    def set_sent_pos_list(self, sent_pos_list):
        self._sent_pos_list = sent_pos_list

    def get_sent_pos_list(self):
        return self._sent_pos_list

    def set_extra(self, extra):
        self._extra = extra

    def get_extra(self):
        return self._extra

    def set_words(self, words):
        self._words = words

    def get_words(self, with_preps=True):
        if not with_preps or not any(e and lp.Attr.PREP_WHITE_LIST in e for e in self._extra):
            return self._words

        preps = [None] * len(self._words)

        for num, extra in enumerate(self._extra):
            if extra and lp.Attr.PREP_WHITE_LIST in extra:
                # this prep should be added after parent
                # TODO why after?
                if self._deps[num]:
                    _, prep_str, _ = extra[lp.Attr.PREP_WHITE_LIST]
                    preps[num + self._deps[num]] = prep_str
        words_with_preps = []
        for num, w in enumerate(self._words):
            words_with_preps.append(w)
            if preps[num]:
                words_with_preps.append(preps[num])

        return words_with_preps

    def set_deps(self, deps):
        self._deps = deps

    def get_deps(self):
        return self._deps

    def set_id_holder(self, pid):
        self._id_holder = pid

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

    def __repr__(self) -> str:
        return f"Phrase(id={self.get_id()}, words= {self.get_words()})"

    def __str__(self):
        return f"Id:{self.get_id()}, words: {self.get_words()}"
