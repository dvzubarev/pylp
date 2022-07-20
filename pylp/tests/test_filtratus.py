#!/usr/bin/env python3

import pytest

from pylp.filtratus import Filtratus
from pylp import lp_doc
from pylp.word_obj import WordObj
from pylp.common import PosTag, SyntLink, Lang


@pytest.fixture
def filtratus():
    kinds = ['punct', 'determiner', 'common_aux', 'stopwords', 'num&undeflang']
    return Filtratus(kinds, {})


def _make_doc_obj(sents):
    doc = lp_doc.Doc('id', lang=Lang.EN)
    for s in sents:
        sent = lp_doc.Sent()
        for w in s:
            sent.add_word(w)
        doc.add_sent(sent)
    return doc


def test_punct(filtratus):
    word1 = WordObj(lemma='a', pos_tag=PosTag.NOUN)
    word2 = WordObj(lemma=',', pos_tag=PosTag.PUNCT)
    word3 = WordObj(lemma='b', pos_tag=PosTag.NOUN)
    word4 = WordObj(lemma='.', pos_tag=PosTag.PUNCT)

    doc = _make_doc_obj([[word1, word2, word3, word4]])
    filtratus('', doc, ['punct'])
    sent1 = doc[0]
    assert len(sent1) == 2
    assert sent1[0].lemma == 'a'
    assert sent1[1].lemma == 'b'


def test_punct_with_synt(filtratus):
    word1 = WordObj(lemma='a', pos_tag=PosTag.NOUN, parent_offs=0, synt_link=SyntLink.ROOT)
    word2 = WordObj(lemma=',', pos_tag=PosTag.PUNCT, parent_offs=-1, synt_link=SyntLink.PUNCT)
    word3 = WordObj(lemma='b', pos_tag=PosTag.NOUN, parent_offs=-2, synt_link=SyntLink.OBJ)
    word4 = WordObj(lemma='.', pos_tag=PosTag.PUNCT, parent_offs=-1, synt_link=SyntLink.PUNCT)

    doc = _make_doc_obj([[word1, word2, word3, word4]])
    filtratus('', doc, ['punct'])
    sent1 = doc[0]
    assert len(sent1) == 2
    assert sent1[0].parent_offs == 0
    assert sent1[1].parent_offs == -1
    assert sent1[1].synt_link == SyntLink.OBJ


# 1       На      на      ADP     _       _       3       case    _       _
# 2       самом   самый   ADJ     _       Case=Loc|Degree=Pos|Gender=Neut|Number=Sing     3       amod    _       _
# 3       деле    дело    NOUN    _       Animacy=Inan|Case=Loc|Gender=Neut|Number=Sing   5       obl     _       _
# 4       я       я       PRON    _       Case=Nom|Number=Sing|Person=1   5       nsubj   _       _
# 5       хотел   хотеть  VERB    _       Aspect=Imp|Gender=Masc|Mood=Ind|Number=Sing|Tense=Past|VerbForm=Fin|Voice=Act   0       root    _       _
# 6       бы      бы      AUX     _       _       5       aux     _       _
# 7       сказать сказать VERB    _       Aspect=Perf|VerbForm=Inf|Voice=Act      5       xcomp   _       SpaceAfter=No
# 8       ,       ,       PUNCT   _       _       14      punct   _       _
# 9       что     что     SCONJ   _       _       14      mark    _       _
# 10      на      на      ADP     _       _       12      case    _       _
# 11      сегодняшний     сегодняшний     ADJ     _       Animacy=Inan|Case=Acc|Degree=Pos|Gender=Masc|Number=Sing        12      amod    _       _
# 12      день    день    NOUN    _       Animacy=Inan|Case=Acc|Gender=Masc|Number=Sing   14      obl     _       _
# 13      я       я       PRON    _       Case=Nom|Number=Sing|Person=1   14      nsubj   _       _
# 14      являюсь являться        VERB    _       Aspect=Imp|Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin|Voice=Mid      7       ccomp   _       _
# 15      одним   один    NUM     _       Case=Ins|Gender=Masc    14      nummod  _       _
# 16      из      из      ADP     _       _       18      case    _       _
# 17      лучших  лучший  ADJ     _       Case=Gen|Degree=Pos|Number=Plur 18      amod    _       _
# 18      сотрудников     сотрудник       NOUN    _       Animacy=Anim|Case=Gen|Gender=Masc|Number=Plur   15      nmod    _       _
# 19      в       в       ADP     _       _       21      case    _       _
# 20      нашей   наш     DET     _       Case=Loc|Gender=Fem|Number=Sing 21      det     _       _
# 21      компании        компания        NOUN    _       Animacy=Inan|Case=Loc|Gender=Fem|Number=Sing    18      nmod    _       SpaceAfter=No
# 22      .       .       PUNCT   _       _       5       punct   _       SpacesAfter=\n


def test_stopwords_with_synt(filtratus):
    kw = {'lang': Lang.EN}
    doc = _make_doc_obj(
        [
            [
                WordObj(lemma='H', pos_tag=PosTag.ADP, parent_offs=2, **kw),
                WordObj(lemma='c', pos_tag=PosTag.ADJ, parent_offs=1, **kw),
                WordObj(lemma='d', pos_tag=PosTag.NOUN, parent_offs=2, **kw),
                WordObj(lemma='ya', pos_tag=PosTag.PRON, parent_offs=1, **kw),
                WordObj(lemma='hot', pos_tag=PosTag.VERB, parent_offs=0, **kw),
                WordObj(lemma='bi', pos_tag=PosTag.AUX, parent_offs=-1, **kw),
                WordObj(lemma='skaz', pos_tag=PosTag.VERB, parent_offs=-2, **kw),
                WordObj(lemma=',', pos_tag=PosTag.PUNCT, parent_offs=6, **kw),
                WordObj(lemma='ct', pos_tag=PosTag.SCONJ, parent_offs=5, **kw),
                WordObj(lemma='na', pos_tag=PosTag.ADP, parent_offs=2, **kw),
                WordObj(lemma='segod', pos_tag=PosTag.ADJ, parent_offs=1, **kw),
                WordObj(lemma='den', pos_tag=PosTag.NOUN, parent_offs=2, **kw),
                WordObj(lemma='ya', pos_tag=PosTag.PRON, parent_offs=1, **kw),
                WordObj(lemma='yavl', pos_tag=PosTag.VERB, parent_offs=-7, **kw),
                WordObj(lemma='odni', pos_tag=PosTag.NUM, parent_offs=-1, **kw),
                WordObj(lemma='iz', pos_tag=PosTag.ADP, parent_offs=2, **kw),
                WordObj(lemma='lucsh', pos_tag=PosTag.ADJ, parent_offs=1, **kw),
                WordObj(lemma='sotr', pos_tag=PosTag.NOUN, parent_offs=-3, **kw),
                WordObj(lemma='v', pos_tag=PosTag.ADP, parent_offs=2, **kw),
                WordObj(lemma='nash', pos_tag=PosTag.DET, parent_offs=1, **kw),
                WordObj(lemma='comp', pos_tag=PosTag.NOUN, parent_offs=-3, **kw),
                WordObj(lemma='.', pos_tag=PosTag.PUNCT, parent_offs=-17, **kw),
            ]
        ]
    )

    filtratus('', doc, ['punct', 'determiner', 'stopwords', 'num&undeflang'])
    sent1 = doc[0]
    assert len(sent1) == 10

    assert sent1[0].lemma == 'c'
    assert sent1[0].parent_offs == 1
    assert sent1[1].lemma == 'd'
    assert sent1[1].parent_offs == 1
    assert sent1[2].lemma == 'hot'
    assert sent1[2].parent_offs == 0
    assert sent1[3].lemma == 'skaz'
    assert sent1[3].parent_offs == -1
    assert sent1[4].lemma == 'segod'
    assert sent1[4].parent_offs == 1
    assert sent1[5].lemma == 'den'
    assert sent1[5].parent_offs == 1
    assert sent1[6].lemma == 'yavl'
    assert sent1[6].parent_offs == -3
    assert sent1[7].lemma == 'lucsh'
    assert sent1[7].parent_offs == 1
    assert sent1[8].lemma == 'sotr'
    assert sent1[8].parent_offs == 0
    assert sent1[8].synt_link == SyntLink.ORPHAN
    assert sent1[9].lemma == 'comp'
    assert sent1[9].parent_offs == -1
