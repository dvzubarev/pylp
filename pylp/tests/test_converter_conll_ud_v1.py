#!/usr/bin/env python3

from pylp.converter_conll_ud_v1 import ConverterConllUDV1
from pylp import common, lp_doc

TEXT_1 = """ Тестовый "текст".

Мама мыла раму, mother washed the frame.
"""

CONLLU_TEXT_ONLY_TOKENS = """# newdoc id = temp
# newpar
# sent_id = 1
# text = Тестовый "текст".
1	Тестовый	_	_	_	_	_	_	_	_
2	"	_	_	_	_	_	_	_	SpaceAfter=No
3	текст	_	_	_	_	_	_	_	SpaceAfter=No
4	"	_	_	_	_	_	_	_	SpaceAfter=No
5	.	_	_	_	_	_	_	_	SpacesAfter=\n

# sent_id = 2
# text = Мама мыла раму, mother washed the frame.
1	Мама	_	_	_	_	_	_	_	_
2	мыла	_	_	_	_	_	_	_	_
3	раму	_	_	_	_	_	_	_	SpaceAfter=No
4	,	_	_	_	_	_	_	_	_
5	mother	_	_	_	_	_	_	_	_
6	washed	_	_	_	_	_	_	_	_
7	the	_	_	_	_	_	_	_	_
8	frame	_	_	_	_	_	_	_	SpaceAfter=No
9	.	_	_	_	_	_	_	_	SpacesAfter=\n

"""

TEXT_2 = """Потрачено.

Мама мыла раму, обещая не работать по выходным.
Потраченная впустую жизнь прекрасна.
"""

CONLLU_TEXT_WITH_TAGS = """# newdoc id = temp
# newpar
# sent_id = 1
# text = Потрачено.
1	Потрачено	тратить	VERB	_	Aspect=Perf|Gender=Neut|Number=Sing|Tense=Past|Variant=Short|VerbForm=Part|Voice=Pass	_	_	_	SpaceAfter=No
2	.	.	PUNCT	_	_	_	_	_	SpacesAfter=\n

# sent_id = 2
# text = Мама мыла раму, обещая не работать по выходным.
1	Мама	мама	NOUN	_	Animacy=Anim|Case=Nom|Gender=Fem|Number=Sing	_	_	_	_
2	мыла	мыть	VERB	_	Aspect=Imp|Gender=Fem|Mood=Ind|Number=Sing|Tense=Past|VerbForm=Fin|Voice=Act	_	_	_	_
3	раму	рама	NOUN	_	Animacy=Inan|Case=Acc|Gender=Fem|Number=Sing	_	_	_	SpaceAfter=No
4	,	,	PUNCT	_	_	_	_	_	_
5	обещая	обещать	VERB	_	Aspect=Imp|Tense=Pres|VerbForm=Conv|Voice=Act	_	_	_	_
6	не	не	RB-ORPH	_	_	_	_	_	_
7	работать	работать	VERB	_	Aspect=Imp|VerbForm=Inf|Voice=Act	_	_	_	_
8	по	по	ADP	_	_	_	_	_	_
9	выходным	выходная	NOUN	_	Animacy=Inan|Case=Dat|Gender=Fem|Number=Plur	_	_	_	SpaceAfter=No
10	.	.	PUNCT	_	_	_	_	_	SpacesAfter=\n

# sent_id = 3
# text = Потраченная впустую жизнь прекрасна.
1	Потраченная	Потраченный	VERB	_	Aspect=Perf|Case=Nom|Gender=Fem|Number=Sing|Tense=Past|VerbForm=Part|Voice=Pass	_	_	_	_
2	впустую	впустой	ADV	_	Degree=Pos	_	_	_	_
3	жизнь	жизнь	NOUN	_	Animacy=Inan|Case=Nom|Gender=Fem|Number=Sing	_	_	_	_
4	прекрасна	прекрасть	ADJ	_	Degree=Pos|Gender=Fem|Number=Sing|Variant=Short	_	_	_	SpaceAfter=No
5	.	.	PUNCT	_	_	_	_	_	SpacesAfter=\n

"""

TEXT_3 = """
Mom, dejected by overwork, was washing a low-standing frame.
Мальчик пишет письмо брату карандашом, the boy writes a letter to his brother with a pencil.
"""

CONLLU_TEXT_WITH_SYNT = """# sent_id = 4
# text = Mom, dejected by overwork, was washing a low-standing frame.
1	Mom	mom	NOUN	_	Number=Sing	8	nsubj	_	SpaceAfter=No
2	,	,	PUNCT	_	_	8	punct	_	_
3	dejected	deject	VERB	_	Tense=Past|VerbForm=Part	8	advcl	_	_
4	by	by	ADP	_	_	5	case	_	_
5	overwork	overwork	NOUN	_	Number=Sing	3	obl	_	SpaceAfter=No
6	,	,	PUNCT	_	_	8	punct	_	_
7	was	be	AUX	_	Mood=Ind|Number=Sing|Person=3|Tense=Past|VerbForm=Fin	8	aux	_	_
8	washing	wash	VERB	_	Tense=Pres|VerbForm=Part	0	root	_	_
9	a	a	DET	_	Definite=Ind|PronType=Art	13	det	_	_
10	low	low	ADJ	_	Degree=Pos	12	amod	_	SpaceAfter=No
11	-	-	PUNCT	_	_	12	punct	_	SpaceAfter=No
12	standing	standing	NOUN	_	Number=Sing	13	compound	_	_
13	frame	frame	NOUN	_	Number=Sing	8	obj	_	SpaceAfter=No
14	.	.	PUNCT	_	_	8	punct	_	SpacesAfter=\n

# sent_id = 5
# text = Мальчик пишет письмо брату карандашом, the boy writes a letter to his brother with a pencil.
1	Мальчик	мальчик	NOUN	_	Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing	2	nsubj	_	_
2	пишет	писать	VERB	_	Aspect=Imp|Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin|Voice=Act	0	root	_	_
3	письмо	письмо	NOUN	_	Animacy=Inan|Case=Acc|Gender=Neut|Number=Sing	2	obj	_	_
4	брату	брат	NOUN	_	Animacy=Anim|Case=Dat|Gender=Masc|Number=Sing	2	iobj	_	_
5	карандашом	карандаш	NOUN	_	Animacy=Inan|Case=Ins|Gender=Masc|Number=Sing	2	obl	_	SpaceAfter=No
6	,	,	PUNCT	_	_	9	punct	_	_
7	the	the	DET	_	Definite=Def|PronType=Art	8	det	_	_
8	boy	boy	NOUN	_	Number=Sing	9	nsubj	_	_
9	writes	write	VERB	_	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	5	acl:relcl	_	_
10	a	a	DET	_	Definite=Ind|PronType=Art	11	det	_	_
11	letter	letter	NOUN	_	Number=Sing	9	obj	_	_
12	to	to	ADP	_	_	14	case	_	_
13	his	he	PRON	_	Gender=Masc|Number=Sing|Person=3|Poss=Yes|PronType=Prs	14	nmod:poss	_	_
14	brother	brother	NOUN	_	Number=Sing	9	obl	_	_
15	with	with	ADP	_	_	17	case	_	_
16	a	a	DET	_	Definite=Ind|PronType=Art	17	det	_	_
17	pencil	pencil	NOUN	_	Number=Sing	9	obl	_	SpaceAfter=No
18	.	.	PUNCT	_	_	2	punct	_	SpacesAfter=\n

"""


def test_only_tokens():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('1')
    converter(TEXT_1, CONLLU_TEXT_ONLY_TOKENS, doc_obj)
    assert len(doc_obj) == 2
    sent1 = doc_obj[0]
    assert len(sent1) == 5
    word1_1 = sent1[0]
    assert word1_1.form == 'Тестовый'
    assert word1_1.lemma == ''
    assert word1_1.offset == 1
    assert word1_1.len == 8

    word1_1 = sent1[2]
    assert word1_1.form == 'текст'
    assert word1_1.lemma == ''
    assert word1_1.offset == 11
    assert word1_1.len == 5
    assert TEXT_1[word1_1.offset : word1_1.offset + word1_1.len] == 'текст'

    sent2 = doc_obj[1]
    assert len(sent2) == 9
    word2_4 = sent2[4]
    assert word2_4.form == 'mother'
    assert TEXT_1[word2_4.offset : word2_4.offset + word2_4.len] == 'mother'


def test_with_tags():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('2')
    converter(TEXT_2, CONLLU_TEXT_WITH_TAGS, doc_obj)
    assert len(doc_obj) == 3

    sent1 = doc_obj[0]
    assert len(sent1) == 2

    # 1	Потрачено	тратить	VERB	_	Aspect=Perf|Gender=Neut|Number=Sing|Tense=Past|Variant=Short|VerbForm=Part|Voice=Pass	_	_	_	SpaceAfter=No
    word1_1 = sent1[0]
    assert word1_1.form == 'Потрачено'
    assert word1_1.lemma == 'тратить'

    assert word1_1.pos_tag == common.PosTag.PARTICIPLE_SHORT
    assert word1_1.gender == common.WordGender.NEUT
    assert word1_1.tense == common.WordTense.PAST
    assert word1_1.voice == common.WordVoice.PASS
    assert word1_1.animacy is None

    # 5	обещая	обещать	VERB	_	Aspect=Imp|Tense=Pres|VerbForm=Conv|Voice=Act	_	_	_	_
    sent2 = doc_obj[1]
    assert len(sent2) == 10
    word2_5 = sent2[4]
    assert word2_5.form == 'обещая'
    assert word2_5.lemma == 'обещать'

    assert word2_5.pos_tag == common.PosTag.PARTICIPLE_ADVERB
    assert word2_5.aspect == common.WordAspect.IMP
    assert word2_5.gender is None

    sent3 = doc_obj[2]
    assert len(sent3) == 5
    # 1	Потраченная	Потраченный	VERB	_	Aspect=Perf|Case=Nom|Gender=Fem|Number=Sing|Tense=Past|VerbForm=Part|Voice=Pass	_	_	_	_
    word3_1 = sent3[0]
    assert word3_1.pos_tag == common.PosTag.PARTICIPLE

    # 4	прекрасна	прекрасть	ADJ	_	Degree=Pos|Gender=Fem|Number=Sing|Variant=Short	_	_	_	SpaceAfter=No

    word3_4 = sent3[3]
    assert word3_4.form == 'прекрасна'
    assert word3_4.lemma == 'прекрасть'  # sic!

    assert word3_4.pos_tag == common.PosTag.ADJ_SHORT
    assert word3_4.gender == common.WordGender.FEM

    print(word3_4.offset)
    assert TEXT_2[word3_4.offset : word3_4.offset + word3_4.len] == 'прекрасна'


def test_lemmas_lower_case():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('3')
    converter(TEXT_2, CONLLU_TEXT_WITH_TAGS, doc_obj)
    assert len(doc_obj) == 3
    sent3 = doc_obj[2]
    word3_1 = sent3[0]
    # all lemma should be lower cased
    assert word3_1.lemma == "потраченный"


def test_with_synt():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('4')
    converter(TEXT_3, CONLLU_TEXT_WITH_SYNT, doc_obj)
    assert len(doc_obj) == 2

    sent2 = doc_obj[1]
    assert len(sent2) == 18
    word2_1 = sent2[0]
    assert word2_1.parent_offs == 1
    assert word2_1.synt_link == common.SyntLink.NSUBJ
    # 2	пишет	писать	VERB	_	Aspect=Imp|Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin|Voice=Act	0	root	_	_
    word2_2 = sent2[1]
    assert word2_2.parent_offs == 0
    assert word2_2.synt_link == common.SyntLink.ROOT

    # 3	письмо	письмо	NOUN	_	Animacy=Inan|Case=Acc|Gender=Neut|Number=Sing	2	obj	_	_
    word2_3 = sent2[2]
    assert word2_3.parent_offs == -1
    assert word2_3.synt_link == common.SyntLink.OBJ
    # 4	брату	брат	NOUN	_	Animacy=Anim|Case=Dat|Gender=Masc|Number=Sing	2	iobj	_	_
    word2_4 = sent2[3]
    assert word2_4.parent_offs == -2
    assert word2_4.synt_link == common.SyntLink.IOBJ
    # 5	карандашом	карандаш	NOUN	_	Animacy=Inan|Case=Ins|Gender=Masc|Number=Sing	2	obl	_	SpaceAfter=No
    word2_5 = sent2[4]
    assert word2_5.parent_offs == -3
    assert word2_5.synt_link == common.SyntLink.OBL


TEXT_4 = """
It comes in silver and black casing and large keys make navigation easy.
"""


CONLLU_TEXT_WITH_SYNT_2 = """# text = It comes in silver and black casing
1	It	it	PRON	PRP	Case=Nom|Gender=Neut|Number=Sing|Person=3|PronType=Prs	2	nsubj	2:nsubj	_
2	comes	come	VERB	VBZ	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	0	root	0:root	_
3	in	in	ADP	IN	_	7	case	7:case	_
4	silver	silver	ADJ	JJ	Degree=Pos	7	amod	7:amod	_
5	and	and	CCONJ	CC	_	6	cc	6:cc	_
6	black	black	ADJ	JJ	Degree=Pos	4	conj	7:amod|4:conj:and	_
7	casing	casing	NOUN	NN	Number=Sing	2	obl	2:obl:in	_

"""


def test_picking_alt_synt_link():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('5')
    converter(TEXT_4, CONLLU_TEXT_WITH_SYNT_2, doc_obj)
    assert len(doc_obj) == 1

    sent1 = doc_obj[0]
    # 6       black   black   ADJ     JJ      Degree=Pos      4       conj    4:conj:and|7:amod       _
    word1_6 = sent1[5]
    assert word1_6.parent_offs == 1
    assert word1_6.synt_link == common.SyntLink.AMOD


TEXT_5 = "he I you"
CONLLU_TEXT_WITH_SYNT_3 = """# text = he I you
1	he	he	PRON	PRP	Case=Nom|Gender=Masc|Number=Sing|Person=3|PronType=Prs	4	nsubj	4:nsubj|6:nsubj:xsubj	_
2	I	I	PRON	PRP	Case=Nom|Number=Sing|Person=1|PronType=Prs	4	conj	4:conj:and|8:nsubj|10:nsubj:xsubj	_
3	you	you	PRON	PRP	Case=Nom|Person=2|PronType=Prs	4	conj	4:conj	_

"""


def test_picking_alt_synt_link_2():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('6')

    converter(TEXT_5, CONLLU_TEXT_WITH_SYNT_3, doc_obj)
    assert len(doc_obj) == 1

    sent1 = doc_obj[0]
    # Select the first from:
    # 4:nsubj|6:nsubj:xsubj
    word1_1 = sent1[0]
    assert word1_1.parent_offs == 3
    assert word1_1.synt_link == common.SyntLink.NSUBJ

    # ignore conj
    # 4:conj:and|8:nsubj
    word1_2 = sent1[1]
    assert word1_2.parent_offs == 2
    assert word1_2.synt_link == common.SyntLink.CONJ

    word1_3 = sent1[2]
    assert word1_3.parent_offs == 1
    assert word1_3.synt_link == common.SyntLink.CONJ


TEXT_6 = "163196 cannot detect"
CONLLU_TEXT_6 = """# text = 163196 cannot detect
3	163196	_	NUM	_	_	1	nmod	_	_
4-5	cannot	_	_	_	_	_	_	_	_
4	can	_	AUX	_	VerbForm=Fin	6	aux	_	_
5	not	_	PART	_	Polarity=Neg	6	advmod	_	_
6	detect	_	VERB	_	VerbForm=Inf	0	root	_	_

"""


def test_skipping_multiword_expressions():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('7')

    converter(TEXT_6, CONLLU_TEXT_6, doc_obj)
    assert len(doc_obj) == 1

    sent1 = doc_obj[0]
    word2 = sent1[1]
    assert word2.form == 'can'
    word3 = sent1[2]
    assert word3.form == 'not'


TEXT_7 = "s/he would assign"
CONLLU_TEXT_7 = """# text = s/he would assign
30	s/he	_	PRON	_	Case=Nom|Gender=Fem,Masc|Number=Sing|Person=3	32	nsubj	_	_
31	would	_	AUX	_	VerbForm=Fin|Gender=unk	32	aux	_	_
32	assign	_	VERB	_	VerbForm=Inf	13	conj	_	_

"""


def test_skipping_multiword_expressions():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('8')

    converter(TEXT_7, CONLLU_TEXT_7, doc_obj)
    assert len(doc_obj) == 1

    sent1 = doc_obj[0]
    word1 = sent1[0]
    assert word1.form == 's/he'
    assert word1.gender == common.WordGender.NONBIN
    word2 = sent1[1]
    assert word2.form == 'would'
    assert word2.gender == common.WordGender.OTHER


TEXT_8 = "Equation 1].\n0=0 if i<4"
CONLLU_TEXT_8 = """# text = Equation 1]. 0=0 if i<4
10	Equation	_	PROPN	_	Number=Sing	2	parataxis	_	_
11	1	_	NUM	_	_	10	dep	_	SpaceAfter=No
12	]. 0=0	_	NUM	_	_	11	flat	_	_
13	if	_	SCONJ	_	_	14	mark	_	_
14	i<4	_	X	_	_	2	parataxis	_	SpaceAfter=No

"""


def test_tokens_with_spaces_1():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('9')

    converter(TEXT_8, CONLLU_TEXT_8, doc_obj)
    assert len(doc_obj) == 1

    sent1 = doc_obj[0]
    word3 = sent1[2]
    assert word3.form == ']. 0=0'
    assert word3.len == 6
    assert word3.offset == 10
    assert TEXT_8[word3.offset : word3.offset + word3.len] == '].\n0=0'


TEXT_8_2 = "Equation 1]. \n 0=0 if i<4"
CONLLU_TEXT_8_2 = """# text = Equation 1]. 0=0 if i<4
10	Equation	_	PROPN	_	Number=Sing	2	parataxis	_	_
11	1	_	NUM	_	_	10	dep	_	SpaceAfter=No
12	]. 0=0	_	NUM	_	_	11	flat	_	_
13	if	_	SCONJ	_	_	14	mark	_	_
14	i<4	_	X	_	_	2	parataxis	_	SpaceAfter=No

"""


def test_tokens_with_spaces_2():
    converter = ConverterConllUDV1()
    doc_obj = lp_doc.Doc('10')

    converter(TEXT_8_2, CONLLU_TEXT_8_2, doc_obj)
    assert len(doc_obj) == 1

    sent1 = doc_obj[0]
    word3 = sent1[2]
    assert word3.form == ']. 0=0'
    assert word3.len == 8
    assert word3.offset == 10
    assert TEXT_8_2[word3.offset : word3.offset + word3.len] == ']. \n 0=0'
