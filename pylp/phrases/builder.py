#!/usr/bin/env python
# coding: utf-8

import math
import logging
import copy
from typing import List, Optional, FrozenSet

import libpyexbase
import pylp.common as lp
from pylp.utils import word_id_combiner


class Sent:
    def __init__(self, sent_word_obj_list, words=None, word_ids: Optional[List] = None, extra=None):
        self._sent_word_obj_list = sent_word_obj_list
        if words is None and word_ids is None:
            raise RuntimeError("Either words or word_ids should be set!")
        self._words = words
        self._word_ids = word_ids
        if extra is None:
            self._extra = [None] * len(sent_word_obj_list)
        else:
            self._extra = extra

    def __len__(self):
        return len(self._sent_word_obj_list)

    def __getitem__(self, index):
        return self._sent_word_obj_list[index]

    def _get_word_obj(self, word_obj_or_pos):
        if isinstance(word_obj_or_pos, dict):
            word_obj = word_obj_or_pos
        elif isinstance(word_obj_or_pos, int):
            word_obj = self._sent_word_obj_list[word_obj_or_pos]
        else:
            raise RuntimeError(f"Unknown argument for word_obj_or_pos {word_obj_or_pos}")
        return word_obj

    def word(self, word_obj_or_pos):
        word_obj = self._get_word_obj(word_obj_or_pos)

        if self._words is not None:
            words = self._words
        elif self._word_ids is not None:
            words = self._word_ids
        else:
            raise RuntimeError("Logic error")
        return words[word_obj[lp.Attr.WORD_NUM]]

    def word_id(self, word_obj_or_pos):
        if self._word_ids is not None:
            word_obj = self._get_word_obj(word_obj_or_pos)
            return self._word_ids[word_obj[lp.Attr.WORD_NUM]]
        return None

    def is_word_undef(self, pos: int):
        return self._sent_word_obj_list[pos][lp.Attr.WORD_NUM] == lp.UNDEF_WORD_NUM

    def set_extra(self, extra):
        self._extra = extra

    def word_extra(self, pos):
        return self._extra[pos]


class PhraseId:
    def __init__(self, pos: int, sent: Sent):
        word_id = self._word_id(pos, sent)

        self._id = word_id
        self._root = word_id
        self._id_parts = [word_id]
        self._prep_id = None

        extra = sent.word_extra(pos)
        if extra is not None and lp.Attr.PREP_WHITE_LIST in extra:
            prep_pos, _ = extra[lp.Attr.PREP_WHITE_LIST]
            self._prep_id = self._word_id(prep_pos, sent)

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

    def _word_id(self, pos: int, sent: Sent):
        word_id = sent.word_id(pos)
        if word_id is None:
            word_str = sent.word(pos)
            word_id = libpyexbase.detect_lang_calc_word_id(word_str, True)
        return word_id

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
    def __init__(self, pos: int = None, sent: Sent = None):
        if pos is not None and sent is not None and not sent.is_word_undef(pos):
            word_obj = sent[pos]
            self._head_pos = 0
            self._sent_pos_list = [pos]
            self._words = [sent.word(word_obj)]

            self._deps = [None]
            self._extra = [sent.word_extra(pos)]

            self._id_holder = PhraseId(pos, sent)

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
                    prep_pos, prep_str = extra[lp.Attr.PREP_WHITE_LIST]
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


def make_2word_phrase(head_phrase: Phrase, mod_phrase: Phrase, sent: Sent):
    head_pos = head_phrase.get_sent_pos_list()[0]
    mod_pos = mod_phrase.get_sent_pos_list()[0]

    p = Phrase()

    mod_on_left = mod_pos < head_pos
    p.set_head_pos(1 if mod_on_left else 0)
    p.set_sent_pos_list([mod_pos, head_pos] if mod_on_left else [head_pos, mod_pos])
    p.set_words([sent.word(p) for p in p.get_sent_pos_list()])
    p.set_deps([1, None] if mod_on_left else [None, -1])

    mod_extra = sent.word_extra(mod_pos)
    head_extra = sent.word_extra(head_pos)
    p.set_extra([mod_extra, head_extra] if mod_pos < head_pos else [head_extra, mod_extra])

    p.set_id_holder(
        copy.copy(head_phrase.get_id_holder()).merge_mod(mod_phrase.get_id_holder(), mod_on_left)
    )
    return p


def _find_insert_pos(head_phrase: Phrase, other_phrase: Phrase):
    head_pos_list = head_phrase.get_sent_pos_list()
    other_pos_list = other_phrase.get_sent_pos_list()
    if head_phrase.sent_hp() < other_phrase.sent_hp():
        # The modificator is on the right side
        insert_pos = len(head_pos_list)
        while other_phrase.sent_hp() < head_pos_list[insert_pos - 1]:
            insert_pos -= 1
    else:
        # The modificator is on the left side
        insert_pos = 0
        while other_phrase.sent_hp() > head_pos_list[insert_pos]:
            insert_pos += 1

    if insert_pos > 0 and head_pos_list[insert_pos - 1] > other_pos_list[0]:
        logging.warning(
            "modificator overlaps with head phrase on the left: head=%s; mod=%s",
            head_phrase,
            other_phrase,
        )
        return None
    if insert_pos < len(head_pos_list) and head_pos_list[insert_pos] < other_pos_list[-1]:
        logging.warning(
            "modificator overlaps with head phrase on the right: head=%s; mod=%s",
            head_phrase,
            other_phrase,
        )
        return None
    return insert_pos


def make_new_phrase(head_phrase: Phrase, other_phrase: Phrase, sent: Sent, phrases_cache):
    new_mod_sz = other_phrase.size()
    old_head_pos = head_pos = head_phrase.get_head_pos()

    head_pos_list = head_phrase.get_sent_pos_list()
    other_on_left = head_phrase.sent_hp() > other_phrase.sent_hp()
    if other_on_left:
        head_pos += new_mod_sz

    insert_pos = _find_insert_pos(head_phrase, other_phrase)
    if insert_pos is None:
        return None

    phrase_signature = (
        head_pos_list[:insert_pos] + other_phrase.get_sent_pos_list() + head_pos_list[insert_pos:]
    )

    t = tuple(phrase_signature)
    if t in phrases_cache:
        return None
    phrases_cache.add(t)

    head_deps = head_phrase.get_deps()
    deps = head_deps[:insert_pos] + other_phrase.get_deps() + head_deps[insert_pos:]
    logging.debug(
        "head_pos: %s, insert pos: %s, head_deps: %s, deps: %s",
        head_pos,
        insert_pos,
        head_deps,
        deps,
    )

    if insert_pos < head_pos:
        i = 0
        while i < insert_pos:
            if i + head_deps[i] == old_head_pos:
                # this is modificator of the root and it should be adjusted
                deps[i] += new_mod_sz
            i += 1
    else:
        i = -1
        while i > insert_pos - len(head_deps) - 1:
            if len(head_deps) + i + head_deps[i] == old_head_pos:
                deps[i] -= new_mod_sz
            i -= 1

    deps[insert_pos + other_phrase.get_head_pos()] = (
        head_pos - insert_pos - other_phrase.get_head_pos()
    )

    words = [sent.word(p) for p in phrase_signature]
    new_phrase = Phrase()
    new_phrase.set_head_pos(head_pos)
    new_phrase.set_words(words)
    new_phrase.set_deps(deps)
    new_phrase.set_extra(
        head_phrase.get_extra()[:insert_pos]
        + other_phrase.get_extra()
        + head_phrase.get_extra()[insert_pos:]
    )

    new_phrase.set_id_holder(
        copy.copy(head_phrase.get_id_holder()).merge_mod(
            other_phrase.get_id_holder(), other_on_left
        )
    )
    new_phrase.set_sent_pos_list(phrase_signature)

    return new_phrase


def _generate_new_phrases(head_phrase, mod_phrases, sent: Sent, phrases_cache):
    for mod_phrase in mod_phrases:
        p = make_new_phrase(head_phrase, mod_phrase, sent, phrases_cache)
        if p is not None:
            yield p


class BasicPhraseBuilderOpts:
    def __init__(self):
        pass


class BasicPhraseBuilder:
    def __init__(self, MaxN, opts: BasicPhraseBuilderOpts = BasicPhraseBuilderOpts()) -> None:
        if MaxN <= 0:
            raise RuntimeError(f"Invalid MaxNumber of words {MaxN}")
        self._max_n = MaxN
        self._opts = opts

    def _create_all_mods_index(self, sent):
        mods_index = [None] * len(sent)

        for i, word_obj in enumerate(sent):
            if word_obj[lp.Attr.WORD_NUM] == lp.UNDEF_WORD_NUM:
                continue

            l = word_obj.get(lp.Attr.SYNTAX_PARENT, 0)
            if l:
                head_pos = i + l
                if mods_index[head_pos] is None:
                    mods_index[head_pos] = []
                mods_index[head_pos].append(i)
        return mods_index

    def _create_indices(self, sent, all_mods_index):
        # words_index:
        # for each word there is a list of size MaxN
        # index 0 -> single words
        # index 1 -> two-word phrases
        # index 3 -> three-word phrases etc...
        # mods_index is modificators of words
        words_index = [None] * len(sent)
        good_mods_index = [None] * len(sent)

        for i, word_obj in enumerate(sent):
            if word_obj[lp.Attr.WORD_NUM] == lp.UNDEF_WORD_NUM:
                continue

            is_good_mod = self._test_pair(word_obj, i, sent, all_mods_index)
            is_good_head = self._test_head(word_obj, i, sent, all_mods_index)

            if is_good_head or is_good_mod:
                words_index[i] = [list() for _ in range(self._max_n)]
                # init words_index's level 0
                words_index[i][0] = [Phrase(i, sent)]

            if is_good_mod:
                head_pos = i + word_obj[lp.Attr.SYNTAX_PARENT]
                if good_mods_index[head_pos] is None:
                    good_mods_index[head_pos] = []
                good_mods_index[head_pos].append(i)

        return words_index, good_mods_index

    def _modifiers_generator(self, modificators, words_index, level, ignore_mods):
        for mod_pos in modificators:
            if mod_pos in ignore_mods:
                continue
            for mod_phrase in words_index[mod_pos][level]:
                yield mod_phrase

    def _generate_phrases(self, words_index, good_mods_index, sent: Sent):
        phrases_cache = set()
        for l in range(1, self._max_n - 1):
            for head_pos, h in enumerate(words_index):
                if h is None:
                    continue
                if not good_mods_index[head_pos]:
                    # no modificators
                    continue
                # extend the phrases from previous levels with modificators
                # e.g. we can take already built 2word phrase, add one modificator and get 3word phrase.
                # or get 2word phrase, add modificator from level 1 that consists of 2 words.
                for head_level, head_phrases in enumerate(words_index[head_pos]):
                    mod_level = l - head_level
                    if mod_level < 0:
                        break
                    for head_phrase in head_phrases:
                        gen = _generate_new_phrases(
                            head_phrase,
                            self._modifiers_generator(
                                good_mods_index[head_pos],
                                words_index,
                                mod_level,
                                head_phrase.get_sent_pos_list(),
                            ),
                            sent,
                            phrases_cache,
                        )
                        for p in gen:
                            words_index[head_pos][l + 1].append(p)

    def _build_phrases_impl(self, sent: Sent):
        logging.debug("sent: %s", sent)

        all_mods_index = self._create_all_mods_index(sent)
        logging.debug("all_mods_index: %s", all_mods_index)

        sent.set_extra(self._create_extra(sent, all_mods_index))

        words_index, good_mods_index = self._create_indices(sent, all_mods_index)
        logging.debug("good_mods_index: %s", good_mods_index)
        logging.debug("words index: %s", words_index)

        # create 2word phrases using sligthly optimized function
        level = 0
        for head_pos, good_mods_list in enumerate(good_mods_index):
            if good_mods_list is None or words_index[head_pos] is None:
                continue

            for mod_pos in good_mods_list:
                p = make_2word_phrase(
                    words_index[head_pos][level][0], words_index[mod_pos][level][0], sent
                )
                words_index[head_pos][level + 1].append(p)

        # fill words_index's levels 2 .. MaxN
        self._generate_phrases(words_index, good_mods_index, sent)

        all_phrases = []
        for head_phrases in words_index:
            if head_phrases is None:
                continue
            for l in range(1, self._max_n):
                for p in head_phrases[l]:
                    all_phrases.append(p)

        return all_phrases

    def _test_pair(self, mod_word_obj, mod_pos, sent, mods_index):
        if not self._test_modifier(mod_word_obj, mod_pos, sent, mods_index):
            return False
        head_pos = mod_pos + mod_word_obj[lp.Attr.SYNTAX_PARENT]
        return self._test_head(sent[head_pos], head_pos, sent, mods_index)

    def _create_extra(self, sent: Sent, mods_index):
        return [None] * len(sent)

    def _test_modifier(self, word_obj: dict, pos: int, sent: Sent, mods_index):
        raise NotImplementedError("_test_modifier")

    def _test_head(self, word_obj: dict, pos: int, sent: Sent, mods_index):
        raise NotImplementedError("_test_head")

    def build_phrases_for_sent(self, sent, words, word_ids=None):
        if len(sent) > 4096:
            raise RuntimeError("Sent size limit!")
        sent = Sent(sent, words, word_ids=word_ids)
        return self._build_phrases_impl(sent)

    def build_phrases_for_sents(self, sents, words, word_ids=None):
        sent_phrases = []
        for sent in sents:
            phrases = self.build_phrases_for_sent(sent, words, word_ids=word_ids)
            sent_phrases.append(phrases)
        return sent_phrases


class PhraseBuilderOpts(BasicPhraseBuilderOpts):
    def __init__(
        self,
        max_syntax_dist=7,
        good_mod_PoS: Optional[FrozenSet[lp.PosTag]] = None,
        good_synt_rels: Optional[FrozenSet[lp.SyntLink]] = None,
        whitelisted_preps: Optional[frozenset] = None,
        good_head_PoS: Optional[FrozenSet[lp.PosTag]] = None,
    ):
        super().__init__()

        self.max_syntax_dist = max_syntax_dist
        self.good_mod_PoS = good_mod_PoS
        if self.good_mod_PoS is None:
            self.good_mod_PoS = frozenset(
                [
                    lp.PosTag.NOUN,
                    lp.PosTag.ADJ,
                    lp.PosTag.NUM,
                    lp.PosTag.PROPN,
                    lp.PosTag.PARTICIPLE,
                    lp.PosTag.PARTICIPLE_SHORT,
                    lp.PosTag.PARTICIPLE_ADVERB,
                    lp.PosTag.ADJ_SHORT,
                ]
            )
        self.good_synt_rels = good_synt_rels
        if self.good_synt_rels is None:
            self.good_synt_rels = frozenset(
                [
                    lp.SyntLink.AMOD,
                    lp.SyntLink.NMOD,
                    lp.SyntLink.COMPOUND,
                    lp.SyntLink.FIXED,
                    lp.SyntLink.FLAT,
                    lp.SyntLink.NUMMOD,
                ]
            )
        self.whitelisted_preps = whitelisted_preps
        if self.whitelisted_preps is None:
            self.whitelisted_preps = lp.PREP_WHITELIST

        self.good_head_PoS = good_head_PoS
        if self.good_head_PoS is None:
            self.good_head_PoS = frozenset([lp.PosTag.NOUN, lp.PosTag.PROPN])


class PhraseBuilder(BasicPhraseBuilder):
    def __init__(self, MaxN, opts: PhraseBuilderOpts = PhraseBuilderOpts()) -> None:
        super().__init__(MaxN, opts=opts)
        self._opts = opts

    def opts(self) -> PhraseBuilderOpts:
        return self._opts

    def _create_preps_info(self, pos, sent: Sent, mods_index):
        preps = []
        whitelisted_preps = []
        modificators = mods_index[pos]
        if modificators is None:
            return {}

        for mod_pos in modificators:
            if mod_pos > pos:
                continue
            mod_obj = sent[mod_pos]

            if (
                mod_obj.get(lp.Attr.POS_TAG) == lp.PosTag.ADP
                and mod_obj.get(lp.Attr.SYNTAX_LINK_NAME) == lp.SyntLink.CASE
            ):
                w = sent.word(mod_obj)
                if w in self.opts().whitelisted_preps:
                    whitelisted_preps.append((mod_pos, w))
                else:
                    preps.append((mod_pos, w))

        extra_dict = {}
        if whitelisted_preps:
            if len(whitelisted_preps) > 1:
                logging.warning(
                    "more than one whitelisted preps: %s choosing only the first one",
                    whitelisted_preps,
                )
            extra_dict[lp.Attr.PREP_WHITE_LIST] = whitelisted_preps[0]
        if preps:
            extra_dict[lp.Attr.PREP_MOD] = preps

        return extra_dict

    def _create_extra(self, sent: Sent, mods_index):
        extras = []
        for pos, word_obj in enumerate(sent):
            extra = {}
            extra.update(self._create_preps_info(pos, sent, mods_index))

            if extra:
                extras.append(extra)
            else:
                extras.append(None)
        return extras

    def _test_pair(self, mod_word_obj, mod_pos, sent, mods_index):
        return super()._test_pair(mod_word_obj, mod_pos, sent, mods_index)

    def _test_nmod(self, word_obj: dict, pos: int, sent: Sent, mods_index):
        """Return true if this nmod without prepositions or with 'of' prep"""
        extra = sent.word_extra(pos)
        if extra is None:
            return True
        return lp.Attr.PREP_WHITE_LIST in extra or lp.Attr.PREP_MOD not in extra

    def _test_modifier(self, word_obj: dict, pos: int, sent: Sent, mods_index):
        """Return True if this is good modifier"""

        if (
            lp.Attr.SYNTAX_PARENT not in word_obj
            or not word_obj[lp.Attr.SYNTAX_PARENT]
            or math.fabs(word_obj[lp.Attr.SYNTAX_PARENT]) > self.opts().max_syntax_dist
            or word_obj.get(lp.Attr.POS_TAG, lp.PosTag.UNDEF) not in self.opts().good_mod_PoS
        ):
            return False

        link = word_obj[lp.Attr.SYNTAX_LINK_NAME]
        if link not in self.opts().good_synt_rels:
            return False

        if link == lp.SyntLink.NMOD:
            if not self._test_nmod(word_obj, pos, sent, mods_index):
                return False

        return True

    def _test_head(self, word_obj: dict, pos: int, sent: Sent, mods_index):
        return word_obj.get(lp.Attr.POS_TAG, lp.PosTag.UNDEF) in self.opts().good_head_PoS
