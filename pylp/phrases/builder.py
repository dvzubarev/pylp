#!/usr/bin/env python
# coding: utf-8

import math
import logging
import copy
from typing import Iterator, List, Optional, FrozenSet, Any, cast
import collections
from collections.abc import Iterable

import pylp.common as lp
from pylp import lp_doc
from pylp.word_obj import WordObj

from pylp.phrases.phrase import Phrase, PhraseType, ReprEnhancer, ReprEnhType

# * Builder helpers


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


def _create_phrase_sent_pos_list(head_phrase: Phrase, other_phrase: Phrase):
    head_pos_list = head_phrase.get_sent_pos_list()
    other_pos_list = other_phrase.get_sent_pos_list()

    new_pos_list = []
    new_head_pos_list: list[int] = [-1] * len(head_pos_list)
    new_other_pos: list[int] = [-1] * len(other_pos_list)
    i = j = 0
    while i < len(head_pos_list) and j < len(other_pos_list):
        if head_pos_list[i] < other_pos_list[j]:
            new_head_pos_list[i] = len(new_pos_list)
            new_pos_list.append(head_pos_list[i])
            i += 1
        elif other_pos_list[j] < head_pos_list[i]:
            new_other_pos[j] = len(new_pos_list)
            new_pos_list.append(other_pos_list[j])
            j += 1
        else:
            raise RuntimeError(
                'trying to merge phrase with the same word: '
                f'head={head_phrase}; other={other_phrase}'
            )
    while i < len(head_pos_list):
        new_head_pos_list[i] = len(new_pos_list)
        new_pos_list.append(head_pos_list[i])
        i += 1
    while j < len(other_pos_list):
        new_other_pos[j] = len(new_pos_list)
        new_pos_list.append(other_pos_list[j])
        j += 1
    return new_pos_list, new_head_pos_list, new_other_pos


def _is_new_phrase_valid(head_phrase: Phrase, other_phrase: Phrase, sent: lp_doc.Sent):
    other_head_modifier = other_phrase.get_head_modifier()
    if (
        other_head_modifier is not None
        and other_head_modifier.prep_modifier is not None
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

    if other_head_modifier is not None and other_head_modifier.prep_modifier is not None:
        prep_str = other_head_modifier.prep_modifier[1]
        repr_enh = ReprEnhancer(-head_pos, ReprEnhType.ADD_WORD, prep_str)
        _add_repr_mod(repr_enh)

    if other_head_modifier is not None and other_head_modifier.repr_mod_suffix is not None:
        repr_enh = ReprEnhancer(0, ReprEnhType.ADD_SUFFIX, other_head_modifier.repr_mod_suffix)
        _add_repr_mod(repr_enh)

    return other_repr_modifiers


def _adjust_deps(new_pos_list, old_deps, new_deps):
    for new_pos, (old_pos, v) in zip(new_pos_list, enumerate(old_deps)):
        if v == 0:
            continue
        old_head_pos = old_pos + v
        new_head_pos = new_pos_list[old_head_pos]
        new_deps[new_pos] = new_head_pos - new_pos


def make_new_phrase(head_phrase: Phrase, other_phrase: Phrase, sent: lp_doc.Sent, phrases_cache):
    if not _is_new_phrase_valid(head_phrase, other_phrase, sent):
        return None

    new_pos_list, new_head_pos_list, new_other_pos_list = _create_phrase_sent_pos_list(
        head_phrase, other_phrase
    )
    new_head_pos = new_head_pos_list[head_phrase.get_head_pos()]

    t = tuple(new_pos_list)
    if t in phrases_cache:
        return None
    phrases_cache.add(t)

    deps = [0] * len(new_pos_list)
    _adjust_deps(new_head_pos_list, head_phrase.get_deps(), deps)
    _adjust_deps(new_other_pos_list, other_phrase.get_deps(), deps)
    other_head_pos = new_other_pos_list[other_phrase.get_head_pos()]
    deps[other_head_pos] = new_head_pos - other_head_pos

    words = [sent[p].lemma for p in new_pos_list]

    other_on_left = head_phrase.sent_hp() > other_phrase.sent_hp()
    id_holder = copy.copy(head_phrase.get_id_holder()).merge_mod(
        other_phrase.get_id_holder(), other_on_left
    )

    def _merge_components(head_comp, other_comp):
        new_comp: list[Any] = [None] * len(new_pos_list)
        for new_pos, v in zip(new_head_pos_list, head_comp):
            new_comp[new_pos] = v
        for new_pos, v in zip(new_other_pos_list, other_comp):
            new_comp[new_pos] = v
        return new_comp

    head_repr_modifiers = head_phrase.get_repr_modifiers()
    other_repr_modifiers = _create_repr_modifiers(other_phrase, sent)
    repr_modifiers = _merge_components(head_repr_modifiers, other_repr_modifiers)

    new_phrase = Phrase(
        size=head_phrase.size() + other_phrase.size(),
        head_pos=new_head_pos,
        words=words,
        deps=deps,
        sent_pos_list=new_pos_list,
        id_holder=id_holder,
        head_modifier=head_phrase.get_head_modifier(),
        repr_modifiers=repr_modifiers,
    )
    # Simply derive type from the head phrase for now
    new_phrase.phrase_type = head_phrase.phrase_type

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
    def __init__(
        self,
        max_variants_bound: int | None = None,
        return_top_level_phrases=False,
        def_phrase_type: PhraseType = PhraseType.DEFAULT,
        propagate_mods_to_conjucts: bool = True,
    ):
        self.max_variants_bound = max_variants_bound
        self.return_top_level_phrases = return_top_level_phrases
        self.def_phrase_type = def_phrase_type
        # See https://fginter.github.io/docs/u/dep/conj.html
        # Propagate all modifiers of the first conjunct to the others.
        # See _propagate_head_modifiers_to_conj for details.
        self.propagate_mods_to_conjucts = propagate_mods_to_conjucts


class BasicPhraseBuilder:
    def __init__(
        self,
        MaxN,
        opts: BasicPhraseBuilderOpts = BasicPhraseBuilderOpts(),
    ) -> None:
        if MaxN <= 0:
            raise RuntimeError(f"Invalid MaxNumber of words {MaxN}")
        self._max_n = MaxN
        self._opts = opts
        self._init_phrases: list[list[Phrase]] = []

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
            add_word_as_phrase = True
            if self._init_phrases and (word_init_phrases := self._init_phrases[pos]):
                # Fill index for this word from init phrases.
                for phrase in word_init_phrases:
                    cur_word_index[min(phrase.size() - 1, self._max_n - 1)].append(phrase)
                    # If this is MWE do not add this word to index
                    if phrase.phrase_type == PhraseType.MWE:
                        add_word_as_phrase = False

            if add_word_as_phrase:
                phrase = Phrase.from_word(pos, word_obj)
                phrase.phrase_type = self._opts.def_phrase_type
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

    def _propagate_head_modifiers_to_conj(self, sent: lp_doc.Sent, aux_indices: AuxBuilderIndices):
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

            # propagate modifiers of the main word to the word conjunct relation
            if self._opts.propagate_mods_to_conjucts and (
                main_word_mods := aux_indices.mods_index[aux_info.main_mod_pos]
            ):
                # See https://fginter.github.io/docs/u/dep/conj.html
                # Since conjuct is a general relation between two elements connected by a conjunction,
                # we use an heuristick to determine whether we should propagate modifiers.
                # We propagate only if current conjuct has no its own modifiers.
                # Also propagate only modificator that placed before main word:
                # amod main, conj2, conj3
                # or after the current conj
                # root_verb, conj_verb obj
                current_mods = aux_indices.mods_index[pos]
                if current_mods is None:
                    current_mods = []
                    current_mods.extend(
                        p for p in main_word_mods if (p < aux_info.main_mod_pos or p > pos)
                    )
                    aux_indices.mods_index[pos] = current_mods

            # propagate cosmetic head modifiers of the main word if any
            if (conj_phrases := aux_indices.words_index[pos]) is None or (
                conj_mod_phrase := _find_phrase(conj_phrases)
            ) is None:
                continue

            if (main_phrases := aux_indices.words_index[aux_info.main_mod_pos]) is None or (
                main_mod_phrase := _find_phrase(main_phrases)
            ) is None:
                continue

            if (
                (conj_head_mod := conj_mod_phrase.get_head_modifier())
                and conj_head_mod.prep_modifier is None
                and (mod_head_mod := main_mod_phrase.get_head_modifier()) is not None
            ):

                conj_head_mod.prep_modifier = mod_head_mod.prep_modifier

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
        self._propagate_head_modifiers_to_conj(sent, aux_indices)
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

            yield from mod_phrases[level]

    def _generate_phrases_for_level(self, level, head_pos, aux_indices, sent, phrases_cache):
        mods_index = aux_indices.mods_index[head_pos]
        if not mods_index:
            # no modificators
            return
        head_index = aux_indices.words_index[head_pos]
        # extend the phrases from previous levels with modificators
        # e.g. we can take already built 2word phrase, add one modificator and get 3word phrase.
        # or get 2word phrase, add modificator from level 1 that consists of 2 words.
        for head_level, head_phrases in enumerate(head_index):
            mod_level = level - head_level
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
                    head_index[level + 1].append(p)
                    # Keep only up to max_variants_bound phrases
                    if (
                        self._opts.max_variants_bound is not None
                        and len(head_index[level + 1]) >= self._opts.max_variants_bound
                    ):
                        return

    def _generate_phrases(self, sent: lp_doc.Sent, aux_indices: AuxBuilderIndices):
        phrases_cache = set()
        # fill words_index's levels 1 .. MaxN
        for l in range(0, self._max_n - 1):
            for head_pos, head_index in enumerate(aux_indices.words_index):
                if head_index is None:
                    continue
                self._generate_phrases_for_level(l, head_pos, aux_indices, sent, phrases_cache)

    def _find_top_level(self, head_index):
        for i in range(self._max_n - 1, 0, -1):
            if head_index[i]:
                return i
        return None

    def _build_phrases_impl(self, sent: lp_doc.Sent):
        logging.debug("sent: %s", sent)

        all_mods_index = self._create_all_mods_index(sent)
        logging.debug("all_mods_index: %s", all_mods_index)

        self._create_extra(sent, all_mods_index)

        aux_indices = self._create_indices(sent, all_mods_index)
        logging.debug("good_mods_index: %s", aux_indices.mods_index)
        logging.debug("words index: %s", aux_indices.words_index)

        self._generate_phrases(sent, aux_indices)

        # Collect all generated phrases.
        all_phrases = []
        for head_phrases in aux_indices.words_index:
            if head_phrases is None:
                continue

            start_level = 1
            if self._opts.return_top_level_phrases:
                start_level = self._find_top_level(head_phrases)
                if start_level is None:
                    continue
            for l in range(start_level, self._max_n):
                for p in head_phrases[l]:
                    pos = p.sent_hp()
                    # Test created phrases. Some phrases suplied via
                    # init_phrases (e.g. MWEs) can be on levels > 0, and they
                    # might have heads not compatible with current builder
                    # settings. We have to remove them from the final phrases list.
                    # See test_add_mwes_to_doc_4
                    if self._test_head(sent[pos], pos, sent, all_mods_index):
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

    def build_phrases_for_sent(
        self, sent: lp_doc.Sent, init_phrases: list[Phrase] | None = None
    ) -> List[Phrase]:
        if len(sent) > 4096:
            raise RuntimeError("Sent size limit!")

        if init_phrases:
            self._init_phrases = [[] for _ in range(len(sent))]
            for p in init_phrases:
                self._init_phrases[p.sent_hp()].append(p)

        else:
            self._init_phrases = []

        return self._build_phrases_impl(sent)


# * Opts and Constants

# Multi word expressions
MWE_RELS = frozenset(
    [
        lp.SyntLink.COMPOUND,
        lp.SyntLink.FIXED,
        lp.SyntLink.FLAT,
    ]
)
VP_RELS = frozenset([lp.SyntLink.OBJ, lp.SyntLink.OBL, lp.SyntLink.IOBJ])

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
        mwe_size=0,
        max_syntax_dist=15,
        good_mod_PoS: FrozenSet[lp.PosTag] | None = None,
        good_synt_rels: FrozenSet[lp.SyntLink] | None = None,
        whitelisted_preps: frozenset | None = None,
        good_head_PoS: FrozenSet[lp.PosTag] | None = None,
        bad_head_rels: FrozenSet[lp.SyntLink] | None = None,
        banned_modifiers: FrozenSet[tuple[str | None, str]] | None = None,
    ):
        super().__init__(
            max_variants_bound=3, return_top_level_phrases=True, def_phrase_type=PhraseType.MWE
        )

        self.mwe_size = mwe_size

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
        propagate_mods_to_conjucts: bool = True,
    ):
        super().__init__(
            max_variants_bound=8, propagate_mods_to_conjucts=propagate_mods_to_conjucts
        )

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


# * Builder class


class PhraseBuilder(BasicPhraseBuilder):
    def __init__(self, MaxN, opts: BasicPhraseBuilderOpts = PhraseBuilderOpts()) -> None:
        super().__init__(MaxN, opts=opts)
        self._opts = opts

        # set by methods
        self._init_phrases = []

    def opts(self) -> PhraseBuilderOpts:
        return cast(PhraseBuilderOpts, self._opts)

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
            (
                None
                if (prep_mod := word_obj.extra.get(lp.Attr.PREP_WHITE_LIST)) is None
                else prep_mod[1]
            ),
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


# * Dispatchers and common builders


def keep_non_overlapping_phrases(phrases: Iterable[Phrase]) -> list[Phrase]:
    """Exclude phrases that are completely overlapped by other phrases. For
    example, if input phrases are [(1, 2), (1,2,3,4), (4,5)] (phrases are
    represented by their positions in the sentence). This function returns
    [(1,2,3,4), (4,5)]. Returned phrases are sorted by the size.
    """

    sorted_phrases = sorted(phrases, key=lambda p: -p.size())
    if not sorted_phrases:
        return []

    seen_phrases: dict[int, list[Phrase]] = collections.defaultdict(list)
    new_phrases = []
    for p in sorted_phrases:
        for pos in p.get_sent_pos_list():
            if (head_phrases := seen_phrases[pos]) and any(hp.contains(p) for hp in head_phrases):
                # phrase is completely overlapped by already added phrase
                break
        else:
            new_phrases.append(p)
            for pos in p.get_sent_pos_list():
                seen_phrases[pos].append(p)

    return new_phrases


class PhraseBuilderProfileArgs:
    def __init__(self, mwe_max_n=0):
        self.mwe_max_n = mwe_max_n


def _noun_phrases(
    sent: lp_doc.Sent, max_n: int, profile_args: PhraseBuilderProfileArgs, builder_cls=PhraseBuilder
) -> list[Phrase]:
    mwe_opts = MWEBuilderOpts(profile_args.mwe_max_n)
    if not mwe_opts.mwe_size:
        mwe_size = max(6, max_n)
    else:
        mwe_size = mwe_opts.mwe_size
    mwe_builder: BasicPhraseBuilder = builder_cls(mwe_size, mwe_opts)

    builder_opts = PhraseBuilderOpts()
    builder: BasicPhraseBuilder = builder_cls(max_n, builder_opts)

    # MWEs are extracted using more efficient greedy algorithm.
    mwes = mwe_builder.build_phrases_for_sent(sent)
    # MWEs could be used to produce other phrases.
    # For example, mod1 + (MWE_head, MWE_mod1, ...)
    # So use them as init phrases, so builder could use them.
    mwes = keep_non_overlapping_phrases(mwes)

    phrases = builder.build_phrases_for_sent(sent, init_phrases=mwes)
    return phrases


def dispatch_phrase_building(
    profile_name: str,
    sent: lp_doc.Sent,
    max_n: int,
    profile_args: PhraseBuilderProfileArgs = PhraseBuilderProfileArgs(),
    builder_cls=PhraseBuilder,
) -> list[Phrase]:
    if profile_name == 'noun_phrases':
        return _noun_phrases(sent, max_n, profile_args, builder_cls)
    if profile_name == 'verb+noun_phrases':
        init_phrases = _noun_phrases(sent, max_n, profile_args, builder_cls)
        builder_opts = PhraseBuilderOpts()
        builder_opts.good_mod_PoS = frozenset([lp.PosTag.NOUN, lp.PosTag.PROPN])
        builder_opts.good_head_PoS = frozenset([lp.PosTag.VERB])
        builder_opts.good_synt_rels = VP_RELS
        builder: BasicPhraseBuilder = builder_cls(max_n, builder_opts)
        vp = builder.build_phrases_for_sent(sent, init_phrases=init_phrases)
        return vp + init_phrases

    raise RuntimeError(f'Unknown profile name: {profile_name}')
