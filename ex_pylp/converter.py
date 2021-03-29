#!/usr/bin/env python
# coding: utf-8

import collections

from ex_pylp.common import PosTag
from ex_pylp.common import Attr
import ex_pylp.common as pylp

def convert_lang(lang_str):
    return pylp.LANG_DICT.get(lang_str.upper(), pylp.Lang.UNDEF)

class SyntConv:
    def __init__(self, calc_stat = False):
        self._calc_stat = calc_stat
        self._stat = None
        if calc_stat:
            self._stat = collections.Counter()

    def _update_stat(self, link_name):
        if self._calc_stat:
            self._stat[link_name] += 1

    def stat(self):
        return self._stat

    def __call__(self, pos, parent_pos, link_name):
        fields = []
        if parent_pos != -1:
            fields.append((Attr.SYNTAX_PARENT, parent_pos - pos))

        #TODO what to do with modificators?
        #nsubj:pass
        #acl:relcl
        #cc:preconj
        fields.append((Attr.SYNTAX_LINK_NAME,
                       pylp.SYNT_LINK_DICT[link_name.split(':', 1)[0].upper()]))

        self._update_stat(link_name)
        return fields

class MorphConv:
    def __init__(self, calc_stat = False):
        self._calc_stat = calc_stat
        self._stat = None
        if calc_stat:
            self._stat = collections.Counter()

    def _update_stat(self, morph_feats):
        if self._calc_stat:
            for feat_name, val in morph_feats.items():
                self._stat["%s_%s" % (feat_name, val)] += 1


    def stat(self):
        return self._stat

    def _adjust_verb(self, morph_feats, fields):
        if 'VerbForm' in morph_feats:
            if morph_feats['VerbForm'] == 'Part':
                if 'Variant' in morph_feats and morph_feats['Variant'] == 'Brev':
                    fields[-1] = (Attr.POS_TAG, PosTag.PARTICIPLE_SHORT)
                else:
                    fields[-1] = ('p', PosTag.PARTICIPLE)
            elif morph_feats['VerbForm'] == 'Ger':
                fields[-1] = (Attr.POS_TAG, PosTag.PARTICIPLE_ADVERB)

    def _adjust_adj(self, morph_feats, fields):
        if 'Variant' in morph_feats and morph_feats['Variant'] == 'Brev':
            fields[-1] = (Attr.POS_TAG, PosTag.ADJ_SHORT)

    def __call__(self, pos, tag, morph_feats):
        fields = []
        if tag:
            if tag == '_':
                pos_tag = pylp.PosTag.UNDEF
            else:
                pos_tag = pylp.POS_TAG_DICT[tag]
            fields.append((Attr.POS_TAG, pos_tag))
            if pos_tag == PosTag.VERB:
                self._adjust_verb(morph_feats, fields)
            elif pos_tag == PosTag.ADJ:
                self._adjust_adj(morph_feats, fields)

        #TODO verb moods? other verb forms Fin? Imp?
        #TODO 'VerbForm' may occur not only for verbs

        if 'Number' in morph_feats:
            n = pylp.WORD_NUMBER_DICT[morph_feats['Number'].upper()]
            if n != pylp.WordNumber.SING:
                fields.append((Attr.PLURAL, n))



        if 'Gender' in morph_feats:
            fields.append((Attr.GENDER, pylp.WORD_GENDER_DICT[morph_feats['Gender'].upper()]))

        if 'Case' in morph_feats:
            fields.append((Attr.CASE, pylp.WORD_CASE_DICT[morph_feats['Case'].upper()]))

        if 'Tense' in morph_feats:
            fields.append((Attr.TENSE, pylp.WORD_TENSE_DICT[morph_feats['Tense'].upper()]))

        if 'Person' in morph_feats:
            fields.append((Attr.PERSON, pylp.WORD_PERSON_DICT[morph_feats['Person'].upper()]))

        if 'Comparision' in morph_feats:
            fields.append((Attr.COMPARISON, pylp.WORD_COMPARISON_DICT[morph_feats['Comparision'].upper()]))

        #TODO skip default
        if 'Aspect' in morph_feats:
            fields.append((Attr.ASPECT, pylp.WORD_ASPECT_DICT[morph_feats['Aspect'].upper()]))

        if 'Voice' in morph_feats:
            v = pylp.WORD_VOICE_DICT[morph_feats['Voice'].upper()]
            if v != pylp.WordVoice.ACT:
                fields.append((Attr.VOICE, v))

        if 'Animacy' in morph_feats:
            a = pylp.WORD_ANIMACY_DICT[morph_feats['Animacy'].upper()]
            if a != pylp.WordAnimacy.INAN:
                fields.append((Attr.ANIMACY, a))

        #TODO valency?

        self._update_stat(morph_feats)
        return fields
