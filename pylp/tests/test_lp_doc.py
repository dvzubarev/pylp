#!/usr/bin/env python3

from pylp.common import Attr, PosTag
from pylp import lp_doc
from pylp.phrases.phrase import Phrase
from pylp.word_obj import WordObj


def filter1(word_obj: WordObj, pos, sent: lp_doc.Sent):
    return word_obj.pos_tag in (PosTag.ADP, PosTag.NUM)


def test_filter_words():
    words = [
        WordObj(lemma='t', pos_tag=PosTag.NOUN),
        WordObj(lemma='on', pos_tag=PosTag.ADP),
        WordObj(lemma='p', pos_tag=PosTag.NOUN),
        WordObj(lemma='o', pos_tag=PosTag.NUM),
    ]
    phrase1 = Phrase(sent_pos_list=[0, 2], words=['t', 'p'])
    phrase2 = Phrase(sent_pos_list=[2, 3], words=['p', 'o'])

    phrases = [phrase1, phrase2]

    sent = lp_doc.Sent(words, phrases)
    sent.filter_words([filter1])

    assert len(sent) == 2
    adjusted_phrases = list(sent.phrases())
    assert len(adjusted_phrases) == 1
    assert adjusted_phrases[0].get_sent_pos_list() == [0, 1]


def test_filter_words_with_with_phrases_1():
    words = [
        WordObj(lemma='r', pos_tag=PosTag.NOUN),
        WordObj(lemma='temp', pos_tag=PosTag.ADP),
        WordObj(lemma='I.', pos_tag=PosTag.NOUN),
        WordObj(lemma='K.', pos_tag=PosTag.NOUN),
    ]
    phrases = [Phrase(sent_pos_list=[2, 3], words=['I.', 'K.'])]

    sent = lp_doc.Sent(words, phrases=phrases)

    sent.filter_words([filter1])

    assert len(sent) == 3
    words = list(sent.words())
    assert len(list(sent.phrases())) == 1
    pos_list = next(sent.phrases()).get_sent_pos_list()
    assert pos_list == [1, 2]


def test_filter_words_with_with_phrases_2():
    words = [
        WordObj(lemma='Thin', pos_tag=PosTag.PROPN),
        WordObj(lemma='Lizzy', pos_tag=PosTag.PROPN),
        WordObj(lemma='temp', pos_tag=PosTag.ADP),
        WordObj(lemma='thin', pos_tag=PosTag.ADJ),
        WordObj(lemma='Lizzy', pos_tag=PosTag.NOUN),
    ]
    phrases = [
        Phrase(sent_pos_list=[0, 1], words=['Thin', 'Lizzy']),
        Phrase(sent_pos_list=[3, 4], words=['thin', 'Lizzy']),
    ]
    sent = lp_doc.Sent(words, phrases=phrases)

    sent.filter_words([filter1])

    assert len(sent) == 4
    words = list(sent.words())
    filt_phrases = list(sent.phrases())
    assert len(filt_phrases) == 2
    pos_list1 = filt_phrases[0].get_sent_pos_list()
    assert pos_list1 == [0, 1]
    assert filt_phrases[1].get_sent_pos_list() == [2, 3]


def test_from_dict():
    doc_dict = {
        'id': 'temp',
        'sents': [
            {'words': [{Attr.POS_TAG: 1, Attr.WORD_FORM: "norm"}]},
            {
                'words': [
                    {Attr.POS_TAG: 2, Attr.WORD_FORM: "norm2"},
                    {Attr.POS_TAG: 3, Attr.WORD_FORM: "norm3"},
                ]
            },
        ],
    }

    doc_obj = lp_doc.Doc.from_dict(doc_dict)

    assert len(doc_obj) == 2
    sent1 = doc_obj[0]
    assert len(sent1) == 1
    w1 = sent1[0]
    assert w1.pos_tag == PosTag.VERB
    assert w1.form == "norm"

    sent2 = doc_obj[1]
    assert len(sent2) == 2
    w2 = sent2[0]
    assert w2.pos_tag == PosTag.NOUN
    assert w2.form == "norm2"
    w3 = sent2[1]
    assert w3.pos_tag == PosTag.ADJ
    assert w3.form == "norm3"

    conv_dict = doc_obj.to_dict()
    del conv_dict['ling_meta']
    assert conv_dict == doc_dict
