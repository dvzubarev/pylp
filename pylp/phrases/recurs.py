#!/usr/bin/env python
# coding: utf-8


import copy
from functools import cmp_to_key
import itertools

# Recursive algo
class Word:
    def __init__(self, pos, word_id):
        self._parent = None
        self._mods = []
        self._pos = pos
        self._word_id = word_id

    def pos(self):
        return self._pos

    def word_id(self):
        return self._word_id

    def childs(self):
        return self._mods

    def add_mod(self, mod):
        mod.set_parent(self)
        self._mods.append(mod)

    def get_parent(self):
        return self._parent

    def set_parent(self, parent):
        self._parent = parent

    def is_root(self):
        return self._parent is None

    def is_leaf(self):
        return not self._mods

    def to_str(self):
        return self._word_id

    def __eq__(self, other):
        return self.pos() == other.pos() and self.word_id() == other.word_id()

    def __hash__(self):
        return hash(repr(self.pos()))

    def __repr__(self):
        return "Word(pos: %s, word_id: %s)" % (self.pos(), self.word_id())

    def __str__(self):
        return "p: %s; id: %s" % (self.pos(), self.word_id())


def _compare_words(w1, w2):
    if w1.is_leaf() and w2.is_leaf() and w1.get_parent() == w2.get_parent():
        i1 = w1.word_id()
        i2 = w2.word_id()
        return -1 if i1 < i2 else int(i1 > i2)
    return w1.pos() - w2.pos()


class NormPhrase:
    """Phrase where modificators are sorted by id, not by pos in the sent."""

    def __init__(self, words, combiner='_'.join):
        self._id = None
        self._words = []
        self._deps = []

        words = list(words)
        words.sort(key=cmp_to_key(_compare_words))
        self._init_phrase(words)

        self._id = combiner(self._words)

    def _init_phrase(self, words):
        temp_dict = {w.pos(): n for n, w in enumerate(words)}
        self._deps = [None] * len(words)
        for pos, w in enumerate(words):
            if w.get_parent():
                self._deps[pos] = temp_dict.get(w.get_parent().pos())
        self._words = [w.word_id() for w in words]

    def get_words(self):
        return self._words

    def get_deps(self):
        return self._deps

    def get_id(self):
        return self._id


def build_words(sent):
    words = [None] * len(sent['words'])
    for mod_pos, head_pos in sent['phrases']:
        if words[head_pos] is None:
            words[head_pos] = Word(head_pos, sent['words'][head_pos])

        if words[mod_pos] is None:
            words[mod_pos] = Word(mod_pos, sent['words'][mod_pos])
        words[head_pos].add_mod(words[mod_pos])
    return words


def build_trees(sent):
    words = build_words(sent)
    return [t for t in words if t is not None and t.is_root()]


def _add_to_phrase(word, phrase_list):
    if not phrase_list:
        phrase_list.append(word)
        return
    i = len(phrase_list)
    while i > 0:
        # if _compare_words(phrase_list[i - 1], word):
        if phrase_list[i - 1].pos() < word.pos():
            phrase_list.insert(i, word)
            break
        i -= 1
    if i == 0:
        phrase_list.insert(0, word)


def _generate_mods_combinations(mods, n):
    if not n:
        return []
    if not mods:
        return []

    for i in range(1, n + 1):
        yield from itertools.combinations(mods, i)


def _build_phrases_recurs(root: Word, cur_phrase, phrases, maxn):
    _add_to_phrase(root, cur_phrase)
    if len(cur_phrase) > 1:
        phrases.add(tuple(cur_phrase))

    if root.is_leaf():
        return

    initial_phrase = copy.copy(cur_phrase)
    childs_comb = _generate_mods_combinations(root.childs(), maxn - len(cur_phrase))
    for comb in childs_comb:
        for child in comb:
            _build_phrases_recurs(child, cur_phrase, phrases, maxn)
            if len(cur_phrase) == maxn:
                break
        cur_phrase = copy.copy(initial_phrase)

    for child in root.childs():
        if child.is_leaf():
            continue

        cur_phrase.clear()
        _build_phrases_recurs(child, cur_phrase, phrases, maxn)


# Entry point for recursive algo
def build_phrases_recurs(sent, MaxN, combiner='_'.join):
    """Recursive algorithm, easy but slow"""
    words_list = set()
    cur_phrase = []
    trees = build_trees(sent)
    for root in trees:
        cur_phrase.clear()
        _build_phrases_recurs(root, cur_phrase, words_list, MaxN)
    linked_words_list = list(words_list)

    phrases = []
    for words in linked_words_list:
        phrases.append(NormPhrase(words, combiner))

    return phrases
