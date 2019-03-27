#!/usr/bin/env python
# coding: utf-8

import enum

def _enum2str(enum_val):
    s = str(enum_val)
    return s[s.index('.') + 1:]

def _make_dict_for_enum(enum_cls, translator = None):
    if translator is None:
        return {_enum2str(v):int(v) for v in enum_cls}
    return {translator[_enum2str(v)]:int(v) for v in enum_cls}

def _make_list_for_enum(enum_cls):
    return [_enum2str(v) for v in enum_cls]

#CONVERTER TABLES

#LANG

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
    ADVCL      = 9
    APPOS      = 10
    AUX        = 11
    CC         = 12
    CCOMP      = 13
    CLF        = 14
    COMPOUND   = 15
    CONJ       = 16
    COP        = 17
    CSUBJ      = 18
    DEP        = 19
    DET        = 20
    DISCOURSE  = 21
    DISLOCATED = 22
    EXPL       = 23
    FIXED      = 24
    FLAT       = 25
    GOESWITH   = 26
    IOBJ       = 27
    LIST       = 28
    MARK       = 29
    NUMMOD     = 30
    ORPHAN     = 31
    PARATAXIS  = 32
    PUNCT      = 33
    REPARANDUM = 34
    VOCATIVE   = 35
    XCOMP      = 36

SYNT_LINK_DICT = _make_dict_for_enum(SyntLink)

#MORPH
class PosTag(enum.IntEnum):
    UNDEF             = 0
    VERB              = 1
    NOUN              = 2
    ADJ               = 3
    PRON              = 4
    NUM               = 5
    PROPN             = 6
    PARENTHESIS       = 7 #compatibility with aot
    INTJ              = 8
    PREDICATE         = 9 #compatibility with aot
    ADP               = 10
    CONJ              = 11
    PART              = 12
    ADV               = 13
    COMPARATIVE       = 14 #compatibility with aot
    ABBREVIATION      = 15 #compatibility with aot
    NUMBER            = 16 #compatibility with aot
    PARTICIPLE        = 17 #полное причастие (aot)
    PARTICIPLE_SHORT  = 18 #краткое причастие (aot)
    PARTICIPLE_ADVERB = 19 #деепричастие (aot)
    ADJ_SHORT         = 20 #краткое прилагательное (aot)
    DET               = 21 #end of aot types
    AUX               = 22
    PUNCT             = 23
    SCONJ             = 24
    CCONJ             = 25
    SYM               = 26
    X                 = 27

POS_TAG_DICT = _make_dict_for_enum(PosTag)

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

class WordComparison(enum.IntEnum):
    SUP = 0
    CMP = 1
WORD_COMPARISON_DICT = _make_dict_for_enum(WordComparison)

class WordAspect(enum.IntEnum):
    IMP  = 0
    PERF = 1

WORD_ASPECT_DICT = _make_dict_for_enum(WordAspect)

class WordVoice(enum.IntEnum):
    ACT  = 0
    PASS = 1
WORD_VOICE_DICT = _make_dict_for_enum(WordVoice)

class WordAnimacy(enum.IntEnum):
    INAN = 0
    ANIM = 1
WORD_ANIMACY_DICT = _make_dict_for_enum(WordAnimacy)



#ATTRIBUTES
class Attr:
    WORD_NUM         = 'i'
    IS_QUESTION      = 'Q'
    LANG             = 'L'
    HOMONYM          = 'H'
    STOP_WORD_TYPE   = 'T'
    SYNTAX_PARENT    = 'l'
    SYNTAX_LINK_NAME = 'n'
    POS_TAG          = 'p'
    PLURAL           = 'P'
    GENDER           = 'g'
    CASE             = 'c'
    TENSE            = 'v'
    PERSON           = '1'
    COMPARISON       = 'C'
    ASPECT           = 'a'
    VOICE            = 'V'
    ANIMACY          = 'A'
    OFFSET           = 'O'
    LENGTH           = 'S'
    ROLES            = 'r'
    RELS             = 'e'
