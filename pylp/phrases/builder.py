#!/usr/bin/env python
# coding: utf-8

import math
import logging
import copy
from typing import Iterator, List, Optional, FrozenSet, Tuple

import pylp.common as lp
from pylp import lp_doc
from pylp.word_obj import WordObj

from pylp.phrases.phrase import Phrase


def make_2word_phrase(head_phrase: Phrase, mod_phrase: Phrase, sent: lp_doc.Sent):
    head_pos = head_phrase.get_sent_pos_list()[0]
    mod_pos = mod_phrase.get_sent_pos_list()[0]

    p = Phrase()

    mod_on_left = mod_pos < head_pos
    p.set_head_pos(1 if mod_on_left else 0)
    p.set_sent_pos_list([mod_pos, head_pos] if mod_on_left else [head_pos, mod_pos])
    p.set_words([sent[p].lemma for p in p.get_sent_pos_list()])
    p.set_deps([1, 0] if mod_on_left else [0, -1])

    mod_extra = copy.copy(sent[mod_pos].extra)
    head_extra = copy.copy(sent[head_pos].extra)
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


def make_new_phrase(head_phrase: Phrase, other_phrase: Phrase, sent: lp_doc.Sent, phrases_cache):
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

    words = [sent[p].lemma for p in phrase_signature]
    new_phrase = Phrase()
    new_phrase.set_head_pos(head_pos)
    new_phrase.set_words(words)
    new_phrase.set_deps(deps)
    new_phrase.set_extra(
        head_phrase.get_extra()[:insert_pos]
        + other_phrase.get_extra()
        + head_phrase.get_extra()[insert_pos:],
        need_copy=True,
    )

    new_phrase.set_id_holder(
        copy.copy(head_phrase.get_id_holder()).merge_mod(
            other_phrase.get_id_holder(), other_on_left
        )
    )
    new_phrase.set_sent_pos_list(phrase_signature)

    return new_phrase


def _generate_new_phrases(
    head_phrase: Phrase, mod_phrases: Iterator[Phrase], sent: lp_doc.Sent, phrases_cache
):
    for mod_phrase in mod_phrases:
        p = make_new_phrase(head_phrase, mod_phrase, sent, phrases_cache)
        if p is not None:
            yield p


# types
PhrasesIndexType = List[Optional[List[List[Phrase]]]]
ModsIndexType = List[Optional[List[int]]]


class BasicPhraseBuilderOpts:
    def __init__(self):
        pass


class BasicPhraseBuilder:
    def __init__(self, MaxN, opts: BasicPhraseBuilderOpts = BasicPhraseBuilderOpts()) -> None:
        if MaxN <= 0:
            raise RuntimeError(f"Invalid MaxNumber of words {MaxN}")
        self._max_n = MaxN
        self._opts = opts

    def _create_all_mods_index(self, sent: lp_doc.Sent) -> ModsIndexType:
        mods_index: ModsIndexType = [None] * len(sent)

        for i, word_obj in enumerate(sent):
            l = word_obj.parent_offs
            if l:
                head_pos = i + l

                mod_list = mods_index[head_pos]
                if mod_list is None:
                    mod_list = [i]
                    mods_index[head_pos] = mod_list
                else:
                    mod_list.append(i)
        return mods_index

    def _create_indices(
        self, sent: lp_doc.Sent, all_mods_index: ModsIndexType
    ) -> Tuple[PhrasesIndexType, ModsIndexType]:
        # words_index:
        # for each word there is a list of size MaxN
        # index 0 -> single words
        # index 1 -> two-word phrases
        # index 3 -> three-word phrases etc...
        # mods_index is modificators of words
        words_index: PhrasesIndexType = [None] * len(sent)
        good_mods_index: ModsIndexType = [None] * len(sent)

        for i, word_obj in enumerate(sent):
            is_good_mod = self._test_pair(word_obj, i, sent, all_mods_index)
            is_good_head = self._test_head(word_obj, i, sent, all_mods_index)

            if is_good_head or is_good_mod:
                try:
                    phrase = Phrase(i, word_obj)
                    cur_word_index = [[] for _ in range(self._max_n)]
                    words_index[i] = cur_word_index
                    # init words_index's level 0
                    cur_word_index[0] = [phrase]
                except RuntimeError as ex:
                    logging.warning("Failed to create phrase from word_obj: %s", ex)

            if is_good_mod and word_obj.parent_offs:
                head_pos = i + word_obj.parent_offs
                mods_list = good_mods_index[head_pos]
                if mods_list is None:
                    good_mods_index[head_pos] = [i]
                else:
                    mods_list.append(i)

        return words_index, good_mods_index

    def _modifiers_generator(
        self,
        modificators: List[int],
        words_index: PhrasesIndexType,
        level: int,
        ignore_mods: List[int],
    ):
        for mod_pos in modificators:
            if mod_pos in ignore_mods:
                continue
            mod_phrases = words_index[mod_pos]
            if mod_phrases is None:
                continue
            for mod_phrase in mod_phrases[level]:
                yield mod_phrase

    def _generate_phrases(
        self, words_index: PhrasesIndexType, good_mods_index: ModsIndexType, sent: lp_doc.Sent
    ):
        phrases_cache = set()
        for l in range(1, self._max_n - 1):
            for head_pos, h in enumerate(words_index):
                if h is None:
                    continue
                mods_index = good_mods_index[head_pos]
                if not mods_index:
                    # no modificators
                    continue
                # extend the phrases from previous levels with modificators
                # e.g. we can take already built 2word phrase, add one modificator and get 3word phrase.
                # or get 2word phrase, add modificator from level 1 that consists of 2 words.
                head_index = words_index[head_pos]
                if head_index is None:
                    continue
                for head_level, head_phrases in enumerate(head_index):
                    mod_level = l - head_level
                    if mod_level < 0:
                        break
                    for head_phrase in head_phrases:
                        gen = _generate_new_phrases(
                            head_phrase,
                            self._modifiers_generator(
                                mods_index,
                                words_index,
                                mod_level,
                                head_phrase.get_sent_pos_list(),
                            ),
                            sent,
                            phrases_cache,
                        )
                        for p in gen:
                            head_index[l + 1].append(p)

    def _build_phrases_impl(self, sent: lp_doc.Sent):
        logging.debug("sent: %s", sent)

        all_mods_index = self._create_all_mods_index(sent)
        logging.debug("all_mods_index: %s", all_mods_index)

        self._create_extra(sent, all_mods_index)

        words_index, good_mods_index = self._create_indices(sent, all_mods_index)
        logging.debug("good_mods_index: %s", good_mods_index)
        logging.debug("words index: %s", words_index)

        # create 2word phrases using sligthly optimized function
        level = 0
        for head_pos, good_mods_list in enumerate(good_mods_index):
            head_index = words_index[head_pos]
            if good_mods_list is None or head_index is None:
                continue

            for mod_pos in good_mods_list:
                mod_index = words_index[mod_pos]
                if mod_index is None:
                    continue
                p = make_2word_phrase(head_index[level][0], mod_index[level][0], sent)
                head_index[level + 1].append(p)

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

    def _test_pair(
        self,
        mod_word_obj: WordObj,
        mod_pos: int,
        sent: lp_doc.Sent,
        mods_index: ModsIndexType,
    ):
        if not mod_word_obj.parent_offs:
            return False

        if not self._test_modifier(mod_word_obj, mod_pos, sent, mods_index):
            return False

        head_pos = mod_pos + mod_word_obj.parent_offs
        return self._test_head(sent[head_pos], head_pos, sent, mods_index)

    def _create_extra(self, sent: lp_doc.Sent, mods_index: ModsIndexType):
        pass

    def _test_modifier(
        self, word_obj: WordObj, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType
    ):
        raise NotImplementedError("_test_modifier")

    def _test_head(self, word_obj: WordObj, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType):
        raise NotImplementedError("_test_head")

    def build_phrases_for_sent(self, sent: lp_doc.Sent):
        if len(sent) > 4096:
            raise RuntimeError("Sent size limit!")
        return self._build_phrases_impl(sent)

    def build_phrases_for_doc(self, doc: lp_doc.Doc):
        for sent in doc:
            phrases = self.build_phrases_for_sent(sent)
            sent.set_phrases(phrases)


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
        if good_mod_PoS is None:
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
        else:
            self.good_mod_PoS = good_mod_PoS
        if good_synt_rels is None:
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
        else:
            self.good_synt_rels = good_synt_rels
        if whitelisted_preps is None:
            self.whitelisted_preps = lp.PREP_WHITELIST
        else:
            self.whitelisted_preps = whitelisted_preps

        if good_head_PoS is None:
            self.good_head_PoS = frozenset([lp.PosTag.NOUN, lp.PosTag.PROPN])
        else:
            self.good_head_PoS = good_head_PoS


class PhraseBuilder(BasicPhraseBuilder):
    def __init__(self, MaxN, opts: PhraseBuilderOpts = PhraseBuilderOpts()) -> None:
        super().__init__(MaxN, opts=opts)
        self._opts = opts

    def opts(self) -> PhraseBuilderOpts:
        return self._opts

    def _create_preps_info(self, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType):
        preps = []
        whitelisted_preps = []
        modificators = mods_index[pos]
        if modificators is None:
            return {}

        for mod_pos in modificators:
            if mod_pos > pos:
                continue
            mod_obj = sent[mod_pos]

            if mod_obj.pos_tag == lp.PosTag.ADP and mod_obj.synt_link == lp.SyntLink.CASE:
                w = mod_obj.lemma
                word_id = mod_obj.word_id
                if w in self.opts().whitelisted_preps:
                    whitelisted_preps.append((mod_pos, w, word_id))
                else:
                    preps.append((mod_pos, w, word_id))

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

    def _create_extra(self, sent: lp_doc.Sent, mods_index: ModsIndexType):
        for pos, word_obj in enumerate(sent):
            extra = self._create_preps_info(pos, sent, mods_index)
            if extra:
                word_obj.extra.update(extra)

    def _test_pair(
        self,
        mod_word_obj: WordObj,
        mod_pos: int,
        sent: lp_doc.Sent,
        mods_index: ModsIndexType,
    ):
        return super()._test_pair(mod_word_obj, mod_pos, sent, mods_index)

    def _test_nmod(self, word_obj: WordObj):
        """Return true if this nmod without prepositions or with whitelisted preposition"""
        extra = word_obj.extra
        return lp.Attr.PREP_WHITE_LIST in extra or lp.Attr.PREP_MOD not in extra

    def _test_modifier(
        self, word_obj: WordObj, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType
    ):
        """Return True if this is good modifier"""

        if (
            not word_obj.parent_offs
            or math.fabs(word_obj.parent_offs) > self.opts().max_syntax_dist
            or word_obj.pos_tag not in self.opts().good_mod_PoS
        ):
            return False

        link = word_obj.synt_link
        if link not in self.opts().good_synt_rels:
            return False

        if link == lp.SyntLink.NMOD:
            if not self._test_nmod(word_obj):
                return False

        return True

    def _test_head(self, word_obj: WordObj, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType):
        return word_obj.pos_tag in self.opts().good_head_PoS
