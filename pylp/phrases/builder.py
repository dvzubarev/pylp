#!/usr/bin/env python
# coding: utf-8

import math
import logging
import copy
from typing import Iterator, List, Optional, FrozenSet

import pylp.common as lp
from pylp import lp_doc
from pylp.word_obj import WordObj

from pylp.phrases.phrase import Phrase, ReprEnhancer, ReprEnhType


def _sorted_lists_intersect(li1, li2):
    i = j = 0
    while i < len(li1) and j < len(li2):
        if li1[i] < li2[j]:
            i += 1
        elif li2[j] < li1[i]:
            j += 1
        else:
            return True

    return False


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


def _is_new_phrase_valid(head_phrase: Phrase, other_phrase: Phrase, sent: lp_doc.Sent):
    other_head_modifier = other_phrase.get_head_modifier()
    if (
        other_head_modifier.prep_modifier is not None
        and other_head_modifier.prep_modifier[0] > other_phrase.get_sent_pos_list()[0]
    ):
        logging.debug(
            "Preposition should be before all modificators: prep=%s, phrase=%s",
            other_head_modifier.prep_modifier,
            other_phrase,
        )
        return False

    return True


def _create_repr_modifiers(other_phrase: Phrase, sent: lp_doc.Sent):

    other_repr_modifiers = copy.copy(other_phrase.get_repr_modifiers())
    other_head_modifier = other_phrase.get_head_modifier()
    head_pos = other_phrase.get_head_pos()

    def _add_repr_mod(repr_enh):
        enh_list = other_repr_modifiers[head_pos]
        if enh_list is None:
            enh_list = []
            other_repr_modifiers[head_pos] = enh_list
        enh_list.append(repr_enh)

    if other_head_modifier.prep_modifier is not None:
        prep_str = other_head_modifier.prep_modifier[1]
        repr_enh = ReprEnhancer(-head_pos, ReprEnhType.ADD_WORD, prep_str)
        _add_repr_mod(repr_enh)

    if other_head_modifier.repr_mod_suffix is not None:
        repr_enh = ReprEnhancer(0, ReprEnhType.ADD_SUFFIX, other_head_modifier.repr_mod_suffix)
        _add_repr_mod(repr_enh)

    return other_repr_modifiers


def make_new_phrase(head_phrase: Phrase, other_phrase: Phrase, sent: lp_doc.Sent, phrases_cache):
    if not _is_new_phrase_valid(head_phrase, other_phrase, sent):
        return None

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
    id_holder = copy.copy(head_phrase.get_id_holder()).merge_mod(
        other_phrase.get_id_holder(), other_on_left
    )

    head_repr_modifiers = head_phrase.get_repr_modifiers()
    other_repr_modifiers = _create_repr_modifiers(other_phrase, sent)

    repr_modifiers = (
        head_repr_modifiers[:insert_pos] + other_repr_modifiers + head_repr_modifiers[insert_pos:]
    )

    new_phrase = Phrase(
        size=head_phrase.size() + new_mod_sz,
        head_pos=head_pos,
        words=words,
        deps=deps,
        sent_pos_list=phrase_signature,
        id_holder=id_holder,
        head_modifier=head_phrase.get_head_modifier(),
        repr_modifiers=repr_modifiers,
    )

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


class AuxBuilderInfo:
    def __init__(self) -> None:
        self.conj_set: List[int] = []
        self.main_mod_pos: int | None = None


class AuxBuilderIndices:
    def __init__(
        self,
        words_index: PhrasesIndexType,
        mods_index: ModsIndexType,
        aux_info_list: List[AuxBuilderInfo | None],
    ):
        self.words_index = words_index
        self.mods_index = mods_index
        self.aux_info_list = aux_info_list


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

    def _init_word_index(self, pos: int, word_obj: WordObj, words_index: PhrasesIndexType):
        try:
            cur_word_index = [[] for _ in range(self._max_n)]
            words_index[pos] = cur_word_index
            if word_obj.mwes:
                mwe_phrase: Phrase
                for mwe_phrase in word_obj.mwes:
                    if mwe_phrase.size() > self._max_n:
                        return
                    cur_word_index[mwe_phrase.size() - 1].append(mwe_phrase)
            else:
                phrase = Phrase.from_word(pos, word_obj)
                # init words_index's level 0
                cur_word_index[0] = [phrase]
        except RuntimeError as ex:
            logging.warning("Failed to create phrase from word_obj: %s", ex)

    def _resolve_conj_modifier(
        self,
        pos: int,
        word_obj: WordObj,
        sent: lp_doc.Sent,
        aux_info_list: List[AuxBuilderInfo | None],
    ):
        init_pos = pos
        # find the actual head of this conj
        link = word_obj.synt_link
        while word_obj.parent_offs and link == lp.SyntLink.CONJ:
            # at first find the modificator with no CONJ type
            conj_pos = pos + word_obj.parent_offs
            conj_obj = sent[conj_pos]

            pos = conj_pos
            word_obj = conj_obj
            link = conj_obj.synt_link

        if init_pos != pos:
            # we skipped all chained conjuncts
            # this word (with index pos) has real dep relation
            # cache this info for init_pos
            aux_info = aux_info_list[init_pos]
            if aux_info is None:
                aux_info = AuxBuilderInfo()
                aux_info_list[init_pos] = aux_info

            aux_info.main_mod_pos = pos

            # collect all conjuct positions in main mod info
            # conj_set is a sorted list
            main_mod_aux_info = aux_info_list[pos]
            if main_mod_aux_info is None:
                main_mod_aux_info = AuxBuilderInfo()
                aux_info_list[pos] = main_mod_aux_info
                main_mod_aux_info.conj_set = [pos]

            insert_pos = len(main_mod_aux_info.conj_set)
            while insert_pos > 0 and init_pos < main_mod_aux_info.conj_set[insert_pos - 1]:
                insert_pos -= 1
            main_mod_aux_info.conj_set.insert(insert_pos, init_pos)
            aux_info.conj_set = main_mod_aux_info.conj_set

        if word_obj.parent_offs:
            return pos + word_obj.parent_offs, word_obj

        return None, None

    def _propagate_head_modifiers_to_conj(self, aux_indices: AuxBuilderIndices):
        def _find_phrase(levels):
            # This word may be MWE, so need to scan all levels
            for phrases_on_level in levels:
                if phrases_on_level:
                    # take the first phrase on a level
                    return phrases_on_level[0]
            return None

        for pos, aux_info in enumerate(aux_indices.aux_info_list):
            # iterate over all words.
            # If a word has main_mod_pos, then it is in conjunct relation.
            # It may be need to propagate some modifiers to this word
            if aux_info is None or aux_info.main_mod_pos is None:
                continue

            if (conj_phrases := aux_indices.words_index[pos]) is None or (
                conj_mod_phrase := _find_phrase(conj_phrases)
            ) is None:
                continue

            if (main_phrases := aux_indices.words_index[aux_info.main_mod_pos]) is None or (
                main_mod_phrase := _find_phrase(main_phrases)
            ) is None:
                continue

            if (
                conj_head_mod := conj_mod_phrase.get_head_modifier()
            ) and conj_head_mod.prep_modifier is None:
                conj_head_mod.prep_modifier = main_mod_phrase.get_head_modifier().prep_modifier

    def _create_indices(
        self, sent: lp_doc.Sent, all_mods_index: ModsIndexType
    ) -> AuxBuilderIndices:
        # words_index:
        # for each word there is a list of size MaxN
        # index 0 -> single words
        # index 1 -> two-word phrases
        # index 3 -> three-word phrases etc...
        # mods_index is modificators of words
        words_index: PhrasesIndexType = [None] * len(sent)
        good_mods_index: ModsIndexType = [None] * len(sent)
        aux_info_list: List[AuxBuilderInfo | None] = [None] * len(sent)

        for i, word_obj in enumerate(sent):
            is_good_head = self._test_head(word_obj, i, sent, all_mods_index)
            if words_index[i] is None and is_good_head:
                self._init_word_index(i, word_obj, words_index)

            if not word_obj.parent_offs:
                continue

            head_pos, mod_word_obj = self._resolve_conj_modifier(i, word_obj, sent, aux_info_list)
            if head_pos is None or mod_word_obj is None:
                continue

            is_good_mod = self._test_pair(head_pos, mod_word_obj, i, sent, all_mods_index)

            if words_index[i] is None and is_good_mod:
                self._init_word_index(i, word_obj, words_index)

            if is_good_mod:
                mods_list = good_mods_index[head_pos]
                if mods_list is None:
                    good_mods_index[head_pos] = [i]
                else:
                    mods_list.append(i)

        aux_indices = AuxBuilderIndices(words_index, good_mods_index, aux_info_list)
        self._propagate_head_modifiers_to_conj(aux_indices)
        return aux_indices

    def _modifiers_generator(
        self,
        modificators: List[int],
        aux_indices: AuxBuilderIndices,
        level: int,
        head_phrase_sent_pos: List[int],
    ):
        for mod_pos in modificators:
            if mod_pos in head_phrase_sent_pos:
                # this modifier is already in phrase
                continue

            aux_info = aux_indices.aux_info_list[mod_pos]
            conj_set = aux_info.conj_set if aux_info is not None else []

            if conj_set:
                # we have to check if the phrase already contains words with conjunct relation to the current modifier.
                # we don't want to combine words with conjunct relation in one phrase,
                # it may become a bit hairy when forming a string representation of a phrase.
                # Especially when phrase also contains prepositions.
                if _sorted_lists_intersect(head_phrase_sent_pos, conj_set):
                    continue

            mod_phrases = aux_indices.words_index[mod_pos]
            if mod_phrases is None:
                continue

            for mod_phrase in mod_phrases[level]:
                yield mod_phrase

    def _generate_phrases(self, sent: lp_doc.Sent, aux_indices: AuxBuilderIndices):
        phrases_cache = set()
        for l in range(0, self._max_n - 1):
            for head_pos, head_index in enumerate(aux_indices.words_index):
                if head_index is None:
                    continue
                mods_index = aux_indices.mods_index[head_pos]
                if not mods_index:
                    # no modificators
                    continue
                # extend the phrases from previous levels with modificators
                # e.g. we can take already built 2word phrase, add one modificator and get 3word phrase.
                # or get 2word phrase, add modificator from level 1 that consists of 2 words.
                for head_level, head_phrases in enumerate(head_index):
                    mod_level = l - head_level
                    if mod_level < 0:
                        break
                    for head_phrase in head_phrases:
                        gen = _generate_new_phrases(
                            head_phrase,
                            self._modifiers_generator(
                                mods_index,
                                aux_indices,
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

        aux_indices = self._create_indices(sent, all_mods_index)
        logging.debug("good_mods_index: %s", aux_indices.mods_index)
        logging.debug("words index: %s", aux_indices.words_index)

        # fill words_index's levels 1 .. MaxN
        self._generate_phrases(sent, aux_indices)

        all_phrases = []
        for head_phrases in aux_indices.words_index:
            if head_phrases is None:
                continue
            for l in range(1, self._max_n):
                for p in head_phrases[l]:
                    pos = p.sent_hp()
                    if self._test_head(sent[pos], pos, sent, all_mods_index):
                        # Some mwe can be on levels > 0, we have to filter them
                        all_phrases.append(p)

        return all_phrases

    def _test_pair(
        self,
        head_pos: int,
        mod_word_obj: WordObj,
        mod_pos: int,
        sent: lp_doc.Sent,
        mods_index: ModsIndexType,
    ):
        return self._test_modifier(mod_word_obj, mod_pos, sent, mods_index) and self._test_head(
            sent[head_pos], head_pos, sent, mods_index
        )

    def _create_extra(self, sent: lp_doc.Sent, mods_index: ModsIndexType):
        pass

    def _test_modifier(
        self, word_obj: WordObj, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType
    ):
        raise NotImplementedError("_test_modifier")

    def _test_head(self, word_obj: WordObj, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType):
        raise NotImplementedError("_test_head")

    def build_phrases_for_sent(self, sent: lp_doc.Sent) -> List[Phrase]:
        if len(sent) > 4096:
            raise RuntimeError("Sent size limit!")
        return self._build_phrases_impl(sent)


# Multi word expressions
MWE_RELS = frozenset(
    [
        lp.SyntLink.COMPOUND,
        lp.SyntLink.FIXED,
        lp.SyntLink.FLAT,
    ]
)
COMMON_BANNED_MODIFIERS = [
    ('число', lp.PosTag.NOUN, 'в'),  # в том числе
    ('целое', lp.PosTag.NOUN, 'в'),  # в целом
    ('случай', lp.PosTag.NOUN, 'в'),  # в случае
    ('среднее', lp.PosTag.NOUN, 'в'),  # в среднем
    ('основной', lp.PosTag.ADJ, 'в'),  # в основном
    ('часть', lp.PosTag.NOUN, 'по'),  # по части
    ('последствие', lp.PosTag.NOUN, 'в'),
    ('итог', lp.PosTag.NOUN, 'в'),
    ('мера', lp.PosTag.NOUN, 'по'),
    ('очередь', lp.PosTag.NOUN, 'в'),
    ('суть', lp.PosTag.NOUN, 'по'),
    ('образ', lp.PosTag.NOUN, None),  # главным образом
    ('степень', lp.PosTag.NOUN, 'в'),  # главным образом
    ('example', lp.PosTag.NOUN, 'for'),
]

# https://universaldependencies.org/v2/mwe.html
class MWEBuilderOpts(BasicPhraseBuilderOpts):
    def __init__(
        self,
        max_syntax_dist=10,
        good_mod_PoS: FrozenSet[lp.PosTag] | None = None,
        good_synt_rels: FrozenSet[lp.SyntLink] | None = None,
        whitelisted_preps: frozenset | None = None,
        good_head_PoS: FrozenSet[lp.PosTag] | None = None,
        bad_head_rels: FrozenSet[lp.SyntLink] | None = None,
        banned_modifiers: FrozenSet[tuple[str | None, str]] | None = None,
    ):
        super().__init__()

        self.max_syntax_dist = max_syntax_dist
        if good_mod_PoS is None:
            self.good_mod_PoS = frozenset(
                [
                    lp.PosTag.NOUN,
                    lp.PosTag.ADJ,
                    lp.PosTag.PARTICIPLE,
                    lp.PosTag.PROPN,
                ]
            )
        else:
            self.good_mod_PoS = good_mod_PoS
        if good_synt_rels is None:
            self.good_synt_rels = MWE_RELS
        else:
            self.good_synt_rels = good_synt_rels

        if whitelisted_preps is None:
            self.whitelisted_preps = lp.PREP_WHITELIST
        else:
            self.whitelisted_preps = whitelisted_preps

        if good_head_PoS is None:
            self.good_head_PoS = frozenset(
                [lp.PosTag.NOUN, lp.PosTag.ADJ, lp.PosTag.PARTICIPLE, lp.PosTag.PROPN]
            )
        else:
            self.good_head_PoS = good_head_PoS

        if bad_head_rels is None:
            self.bad_head_rels = []
        else:
            self.bad_head_rels = bad_head_rels

        if banned_modifiers is None:
            self.banned_modifiers = frozenset()
        else:
            self.banned_modifiers = banned_modifiers


class PhraseBuilderOpts(BasicPhraseBuilderOpts):
    def __init__(
        self,
        max_syntax_dist=30,
        good_mod_PoS: FrozenSet[lp.PosTag] | None = None,
        good_synt_rels: FrozenSet[lp.SyntLink] | None = None,
        whitelisted_preps: frozenset | None = None,
        good_head_PoS: FrozenSet[lp.PosTag] | None = None,
        bad_head_rels: FrozenSet[lp.SyntLink] | None = None,
        banned_modifiers: FrozenSet[tuple[str, lp.PosTag, str | None]] | None = None,
    ):
        super().__init__()

        self.max_syntax_dist = max_syntax_dist
        if good_mod_PoS is None:
            self.good_mod_PoS = frozenset(
                [
                    lp.PosTag.NOUN,
                    lp.PosTag.PROPN,
                    lp.PosTag.ADJ,
                    lp.PosTag.PROPN,
                    lp.PosTag.PARTICIPLE,
                    lp.PosTag.PARTICIPLE_SHORT,
                    lp.PosTag.GERUND,
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

        if bad_head_rels is None:
            self.bad_head_rels = MWE_RELS
        else:
            self.bad_head_rels = bad_head_rels

        if banned_modifiers is None:
            self.banned_modifiers = frozenset(COMMON_BANNED_MODIFIERS)
        else:
            self.banned_modifiers = banned_modifiers


class PhraseBuilder(BasicPhraseBuilder):
    def __init__(self, MaxN, opts: BasicPhraseBuilderOpts = PhraseBuilderOpts()) -> None:
        super().__init__(MaxN, opts=opts)
        self._opts = opts

    def opts(self) -> PhraseBuilderOpts:
        return self._opts

    def _restore_prep_str(self, prep_pos: int, prep_obj: WordObj, sent: lp_doc.Sent):
        beg = max(0, prep_pos - 2)
        end = min(len(sent), prep_pos + 3)

        prep_str = prep_obj.lemma
        for i in range(beg, end):
            word_obj = sent[i]
            if (
                word_obj.parent_offs
                and word_obj.parent_offs + i == prep_pos
                and word_obj.synt_link == lp.SyntLink.FIXED
            ):
                if i < prep_pos:
                    return f'{word_obj.lemma} {prep_str}'
                return f'{prep_str} {word_obj.lemma}'
        return prep_str

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
                prep_str = self._restore_prep_str(mod_pos, mod_obj, sent)
                word_id = mod_obj.word_id
                if prep_str in self.opts().whitelisted_preps:
                    whitelisted_preps.append((mod_pos, prep_str, word_id))
                else:
                    preps.append((mod_pos, prep_str, word_id))

        extra_dict = {}
        if whitelisted_preps:
            selected_prep = whitelisted_preps[-1]
            if len(whitelisted_preps) > 1:
                logging.debug(
                    "more than one whitelisted preps: %s choosing the closest to the word: %s",
                    whitelisted_preps,
                    sent[pos],
                )

            extra_dict[lp.Attr.PREP_WHITE_LIST] = selected_prep
        if preps:
            extra_dict[lp.Attr.PREP_MOD] = preps

        return extra_dict

    def _create_repr_modifiers_info(self, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType):
        modificators = mods_index[pos]
        if modificators is None:
            return {}

        for mod_pos in modificators:
            mod_obj = sent[mod_pos]
            if (
                mod_obj.pos_tag == lp.PosTag.PART
                and mod_obj.synt_link == lp.SyntLink.CASE
                and mod_obj.lemma in ("'s", "'")
            ):
                return {lp.Attr.REPR_MOD_SUFFIX: mod_obj.lemma}

        return {}

    def _create_extra(self, sent: lp_doc.Sent, mods_index: ModsIndexType):
        for pos, word_obj in enumerate(sent):
            extra = self._create_preps_info(pos, sent, mods_index)
            extra.update(self._create_repr_modifiers_info(pos, sent, mods_index))
            if extra:
                word_obj.extra.update(extra)

    def _test_pair(
        self,
        head_pos: int,
        mod_word_obj: WordObj,
        mod_pos: int,
        sent: lp_doc.Sent,
        mods_index: ModsIndexType,
    ):
        return super()._test_pair(head_pos, mod_word_obj, mod_pos, sent, mods_index)

    def _test_nmod(self, word_obj: WordObj):
        """Return true if this nmod without prepositions or with whitelisted preposition"""
        extra = word_obj.extra
        return word_obj.pos_tag in (lp.PosTag.NOUN, lp.PosTag.PROPN) and (
            lp.Attr.PREP_WHITE_LIST in extra or lp.Attr.PREP_MOD not in extra
        )

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

        key = (
            word_obj.lemma,
            word_obj.pos_tag,
            None
            if (prep_mod := word_obj.extra.get(lp.Attr.PREP_WHITE_LIST)) is None
            else prep_mod[1],
        )
        if key in self.opts().banned_modifiers:
            return False

        link = word_obj.synt_link
        if link not in self.opts().good_synt_rels:
            return False

        if link == lp.SyntLink.NMOD:
            if not self._test_nmod(word_obj):
                return False

        return True

    def _test_head(self, word_obj: WordObj, pos: int, sent: lp_doc.Sent, mods_index: ModsIndexType):
        return (
            not word_obj.lang == lp.Lang.UNDEF
            and word_obj.pos_tag in self.opts().good_head_PoS
            and word_obj.synt_link not in self.opts().bad_head_rels
        )
