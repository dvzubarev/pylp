#!/usr/bin/env python
# coding: utf-8

import collections
import logging
import copy
from functools import cmp_to_key
import itertools


import pylp.common as lp
from pylp.utils import word_id_combiner


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


# Iterative algorithm
class PhraseMerger:
    @classmethod
    def mod_head2phrase(cls, mod_pos, head_pos, sent_words, combiner='_'.join, extra=None):
        # pylint: disable=protected-access
        if sent_words[mod_pos] is None or sent_words[head_pos] is None:
            return None

        if extra is None:
            extra = [None] * len(sent_words)
        p = cls()
        p.set_combiner(combiner)
        p._head_pos = 1 if mod_pos < head_pos else 0
        p.set_sent_pos_list([mod_pos, head_pos] if mod_pos < head_pos else [head_pos, mod_pos])
        p.set_words([sent_words[p] for p in p.get_sent_pos_list()])

        p.set_deps([1, None] if mod_pos < head_pos else [None, -1])
        p.set_extra(
            [extra[mod_pos], extra[head_pos]]
            if mod_pos < head_pos
            else [extra[head_pos], extra[mod_pos]]
        )

        p.set_id(combiner(p.get_words()))
        return p

    def __init__(self, head_pos=None, sent_words=None, combiner='_'.join, extra=None):

        if head_pos is not None:
            self._head_pos = 0
            self._sent_pos_list = [head_pos]
            self._words = [sent_words[head_pos]]

            self._deps = [None]
            self._extra = [None]

            self._id = self._words[0]
        self._combiner = combiner

    def size(self):
        return len(self._words)

    def sent_hp(self):
        return self._sent_pos_list[self._head_pos]

    def maybe_make_new_phrase(self, other_phrase, sent_words, phrases_cache):
        # pylint: disable=protected-access
        new_mod_sz = other_phrase.size()
        head_pos = self._head_pos

        if self.sent_hp() < other_phrase.sent_hp():
            # The modificator is on the right side
            insert_pos = len(self._sent_pos_list)
            while other_phrase.sent_hp() < self._sent_pos_list[insert_pos - 1]:
                insert_pos -= 1
        else:
            # The modificator is on the left side
            head_pos += new_mod_sz
            insert_pos = 0
            while other_phrase.sent_hp() > self._sent_pos_list[insert_pos]:
                insert_pos += 1

        phrase_signature = (
            self._sent_pos_list[:insert_pos]
            + other_phrase.get_sent_pos_list()
            + self._sent_pos_list[insert_pos:]
        )

        t = tuple(phrase_signature)
        if t in phrases_cache:
            return None
        phrases_cache.add(t)

        deps = self._deps[:insert_pos] + other_phrase.get_deps() + self._deps[insert_pos:]

        if insert_pos < head_pos:
            i = 0
            while i < insert_pos:
                if i + self._deps[i] == self._head_pos:
                    # this is modificator of the root and it should be adjusted
                    deps[i] += new_mod_sz
                i += 1
        else:
            i = -1
            while i > insert_pos - len(self._deps) - 1:
                if len(self._deps) + i + self._deps[i] == self._head_pos:
                    deps[i] -= new_mod_sz
                i -= 1

        deps[insert_pos + other_phrase._head_pos] = head_pos - insert_pos - other_phrase._head_pos

        words = [sent_words[p] for p in phrase_signature]
        # phrase_id  = self._combiner(words)
        new_phrase = PhraseMerger()
        new_phrase._head_pos = head_pos
        new_phrase.set_words(words)
        new_phrase.set_deps(deps)
        new_phrase.set_extra(
            self._extra[:insert_pos] + other_phrase._extra + self._extra[insert_pos:]
        )

        new_phrase.set_id(self._combiner(new_phrase.get_words()))
        new_phrase.set_sent_pos_list(phrase_signature)
        new_phrase.set_combiner(self._combiner)

        return new_phrase

    def make_new_phrase(self, other_phrase, sent_words):
        return self.maybe_make_new_phrase(other_phrase, sent_words, set())

    def set_combiner(self, combiner):
        self._combiner = combiner

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
        if not with_preps:
            return self._words

        preps = [None] * len(self._words)

        for num, extra in enumerate(self._extra):
            if extra and lp.Attr.PREP_MOD in extra:
                # this prep should be added after parent
                # TODO why after?
                if self._deps[num]:
                    preps[num + self._deps[num]] = extra[lp.Attr.PREP_MOD]
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

    def set_id(self, pid):
        self._id = pid

    def get_id(self):
        return self._id


def _maybe_generate_new_phrases(head_phrase, mod_phrases, phrases_cache, words):

    for mod_phrase in mod_phrases:
        p = head_phrase.maybe_make_new_phrase(mod_phrase, words, phrases_cache)
        if p is not None:
            yield p


def _mods_generator(modificators, words_index, level, ignore_mods):
    for mod_pos in modificators:
        if mod_pos in ignore_mods:
            continue
        for mod_phrase in words_index[mod_pos][level]:
            yield mod_phrase


def _init_word(pos, words_index, MaxN, words, combiner, extra):
    if words[pos] is None:
        return
    words_index[pos] = [list() for _ in range(MaxN)]
    words_index[pos][0] = [PhraseMerger(pos, words, combiner=combiner, extra=extra)]


# Entry point for iterative algo
def build_phrases_iter(sent, MaxN=4, combiner='_'.join):
    if MaxN <= 0:
        return []

    if not sent['phrases']:
        return []

    if len(sent['words']) > 4096:
        raise RuntimeError("Sent size limit!")

    # words and phrases: its a list of lists
    # for each word there is a list of size MaxN
    # index 0 -> single words
    # index 1 -> two-word phrases
    # index 3 -> three-word phrases etc...
    words_index = [None] * len(sent['words'])
    # modificators of words
    mods_index = [None] * len(sent['words'])

    # init words_index's levels 0 and 1
    # also fill mods_index
    for mod_pos, head_pos in sent['phrases']:
        if words_index[head_pos] is None:
            # init head
            _init_word(
                head_pos, words_index, MaxN, sent['words'], combiner, sent['extra'][head_pos]
            )
        p = PhraseMerger.mod_head2phrase(
            mod_pos, head_pos, sent['words'], combiner=combiner, extra=sent['extra']
        )

        if p is not None:
            words_index[head_pos][1].append(p)

        if mods_index[head_pos] is None:
            mods_index[head_pos] = []

        if sent['words'][mod_pos] is not None:
            mods_index[head_pos].append(mod_pos)

        if words_index[mod_pos] is None:
            _init_word(mod_pos, words_index, MaxN, sent['words'], combiner, sent['extra'][mod_pos])

    # fill words_index's levels 2 .. MaxN
    phrases_cache = set()
    for l in range(1, MaxN - 1):
        for head_pos, h in enumerate(words_index):
            if h is None:
                continue
            if mods_index[head_pos] is None:
                # this is only modificator
                continue
            # extend the phrases from previous levels with modificators
            # e.g. we can take already built 2word phrase, add one modificator and get 3word phrase.
            # or get 2word phrase, add modificator from level 1 that consists of 2 words.
            for head_level, head_phrases in enumerate(words_index[head_pos]):
                mod_level = l - head_level
                if mod_level < 0:
                    break
                for head_phrase in head_phrases:
                    gen = _maybe_generate_new_phrases(
                        head_phrase,
                        _mods_generator(
                            mods_index[head_pos],
                            words_index,
                            mod_level,
                            head_phrase.get_sent_pos_list(),
                        ),
                        phrases_cache,
                        sent['words'],
                    )
                    for p in gen:
                        words_index[head_pos][l + 1].append(p)

    all_phrases = []
    for head_phrases in words_index:
        if head_phrases is None:
            continue
        for l in range(1, MaxN):
            for p in head_phrases[l]:
                all_phrases.append(p)

    return all_phrases


# common stuff


def remove_rare_phrases(sents, min_cnt=1):
    if min_cnt <= 0:
        return sents

    counter = collections.Counter()
    for sent in sents:
        for w in sent:
            if isinstance(w, dict):
                counter[w['id']] += 1
    new_sents = []
    for sent in sents:
        new_sent = []
        for w in sent:
            if not isinstance(w, dict):
                new_sent.append(w)
                continue
            if counter[w['id']] >= min_cnt:
                new_sent.append(w)

        new_sents.append(new_sent)

    return new_sents


def create_sents_with_phrases(
    sents, MaxN, combiner=word_id_combiner, min_cnt=0, algo=build_phrases_iter, create_mode='append'
):
    def _phrase_to_dict(phrase):
        return {
            "id": phrase.get_id(),
            "components": phrase.get_words(with_preps=False),
            "deps": phrase.get_deps(),
            "extra": phrase.get_extra(),
        }

    if create_mode not in ['append', 'replace']:
        raise RuntimeError("Unknown create_mode: %s" % create_mode)

    sents_with_phrases = []
    for sent in sents:
        phrases = algo(sent, MaxN=MaxN, combiner=combiner)
        if create_mode == 'append':
            sents_with_phrases.append(sent['words'])
            for phrase in phrases:
                sents_with_phrases[-1].append(_phrase_to_dict(phrase))
        elif create_mode == 'replace':
            new_sent = replace_words_with_phrases(sent['words'], phrases)
            for pos, w in enumerate(new_sent):
                if isinstance(w, PhraseMerger):
                    new_sent[pos] = _phrase_to_dict(w)
            sents_with_phrases.append(new_sent)

    return remove_rare_phrases(sents_with_phrases, min_cnt=min_cnt)


def replace_words_with_phrases(words, phrases):
    """phrases are list of prhases from the build_phrases_iter function"""

    if not phrases:
        return words

    phrases.sort(key=lambda p: -p.size())

    new_sent = list(range(len(words)))
    logging.debug("new sent: %s", new_sent)
    for p in phrases:
        # TODO make it optional all or any
        if all(isinstance(new_sent[pos], tuple) for pos in p.get_sent_pos_list()):
            # overlapping with other phrase
            continue
        added = False
        for pos in p.get_sent_pos_list():
            if not isinstance(new_sent[pos], tuple):
                if not added:
                    new_sent[pos] = (p,)
                    added = True
                else:
                    new_sent[pos] = tuple()

    logging.debug("sent with phrases: %s", new_sent)
    return [w[0] if isinstance(w, tuple) else words[w] for w in new_sent if w != ()]
