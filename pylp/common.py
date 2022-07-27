#!/usr/bin/env python
# coding: utf-8

import enum


def enum2str(enum_val):
    s = str(enum_val)
    return s[s.index('.') + 1 :]


def _make_dict_for_enum(enum_cls, translator=None):
    if translator is None:
        return {enum2str(v): v for v in enum_cls}
    return {translator[enum2str(v)]: v for v in enum_cls}


def _make_list_for_enum(enum_cls):
    return [enum2str(v) for v in enum_cls]


# CONVERTER TABLES

# LANG

# fmt: off
class Lang(enum.IntEnum):
    RU    = 0
    EN    = 1
    UNDEF = 15

LANG_DICT = _make_dict_for_enum(Lang)


#SYNTAX
# UD version 2
class SyntLink(enum.IntEnum):
    ROOT       = 0
    NSUBJ      = 1
    OBJ        = 2
    OBL        = 3
    ADVMOD     = 4
    AMOD       = 5
    NMOD       = 6
    CASE       = 7
    ACL        = 8
    CC         = 9
    APPOS      = 10
    COMPOUND   = 11
    CONJ       = 12
    DEP        = 13
    MARK       = 14
    NUMMOD     = 15
    AUX        = 16
    FLAT       = 17
    CCOMP      = 18
    CLF        = 19
    COP        = 20
    CSUBJ      = 21
    ADVCL      = 22
    DET        = 23
    DISCOURSE  = 24
    DISLOCATED = 25
    EXPL       = 26
    FIXED      = 27
    GOESWITH   = 28
    IOBJ       = 29
    LIST       = 30
    ORPHAN     = 31
    PARATAXIS  = 32
    PUNCT      = 33
    REPARANDUM = 34
    VOCATIVE   = 35
    XCOMP      = 36

SYNT_LINK_DICT = _make_dict_for_enum(SyntLink)

#MORPH
class PosTag(enum.IntEnum):
    PROPN             = 0
    VERB              = 1
    NOUN              = 2
    ADJ               = 3
    PRON              = 4
    NUM               = 5
    PARTICIPLE        = 6 #полное причастие
    PARTICIPLE_SHORT  = 7 #краткое причастие
    PARTICIPLE_ADVERB = 8 #деепричастие
    ADJ_SHORT         = 9 #краткое прилагательное
    ADP               = 10
    PART              = 11
    ADV               = 12
    CCONJ             = 13
    SCONJ             = 14
    SYM               = 15
    AUX               = 16
    DET               = 17
    X                 = 18
    INTJ              = 19
    CONJ              = 20
    PUNCT             = 21
    UNDEF             = 22



POS_TAG_DICT = _make_dict_for_enum(PosTag)

STOP_WORD_POS_TAGS = [PosTag.UNDEF,
                      PosTag.PUNCT,
                      PosTag.DET,
                      PosTag.AUX,
                      PosTag.CONJ,
                      PosTag.CCONJ,
                      PosTag.SCONJ,
                      PosTag.SYM,
                      PosTag.X,
                      PosTag.PART,
                      PosTag.ADP,
                      PosTag.PRON]

class WordNumber(enum.IntEnum):
    SING = 0
    PLUR = 1

WORD_NUMBER_DICT = _make_dict_for_enum(WordNumber)

class WordGender(enum.IntEnum):
    UNDEF = 0
    MASC  = 1
    FEM   = 2
    NEUT  = 3

WORD_GENDER_DICT = _make_dict_for_enum(WordGender)

class WordCase(enum.IntEnum):
    NOM = 0
    GEN = 1
    ACC = 2
    DAT = 3
    INS = 4
    LOC = 5
    PAR = 6
    VOC = 7
WORD_CASE_DICT = _make_dict_for_enum(WordCase)

class WordTense(enum.IntEnum):
    PRES = 0
    PAST = 1
    IMP  = 2
    FUT  = 3
    PQP  = 4
WORD_TENSE_DICT = _make_dict_for_enum(WordTense)

class WordPerson(enum.IntEnum):
    I   = 0
    II  = 1
    III = 2
WORD_PERSON_DICT = _make_dict_for_enum(WordPerson, {'I': '1', 'II': '2', 'III': '3'})

class WordDegree(enum.IntEnum):
    POS = 0
    EQU = 1
    CMP = 2
    SUP = 3
    ABS = 4

WORD_DEGREE_DICT = _make_dict_for_enum(WordDegree)

class WordAspect(enum.IntEnum):
    IMP  = 0
    PERF = 1

WORD_ASPECT_DICT = _make_dict_for_enum(WordAspect)

class WordVoice(enum.IntEnum):
    ACT  = 0
    PASS = 1
    MID = 2
WORD_VOICE_DICT = _make_dict_for_enum(WordVoice)

class WordMood(enum.IntEnum):
    IND = 0
    IMP = 1
    CND = 2
WORD_MOOD_DICT = _make_dict_for_enum(WordMood)

class WordNumType(enum.IntEnum):
    CARD = 0
    ORD = 1
    MULT = 2
    FRAC = 3
    RANGE = 4
WORD_NUM_TYPE_DICT = _make_dict_for_enum(WordNumType)

class WordAnimacy(enum.IntEnum):
    INAN = 0
    ANIM = 1
WORD_ANIMACY_DICT = _make_dict_for_enum(WordAnimacy)


UNDEF_WORD_NUM = -1

#ATTRIBUTES
class Attr:
    WORD_NUM         = 'i'
    WORD_FORM        = 'form'
    WORD_LEMMA       = 'lemma'
    WORD_ID          = 'id'
    IS_QUESTION      = 'Q'
    LANG             = 'L'
    HOMONYM          = 'H'
    STOP_WORD_TYPE   = 'T'
    SYNTAX_PARENT    = 'l'
    SYNTAX_LINK_NAME = 'n'
    POS_TAG          = 'p'
    NUMBER           = 'P'
    GENDER           = 'g'
    CASE             = 'c'
    TENSE            = 'v'
    PERSON           = '1'
    DEGREE           = '>'
    ASPECT           = 'a'
    VOICE            = 'V'
    MOOD             = 'm'
    NUM_TYPE         = '#'
    ANIMACY          = 'A'
    OFFSET           = 'O'
    LENGTH           = 'S'
    ROLES            = 'r'
    RELS             = 'e'
    PREP_MOD         = 'M'
    #TEMP
    PREP_WHITE_LIST  = 'W'

PREP_WHITELIST = frozenset([
    "of",
    18370182862529888470,  # of

])
# fmt: on
