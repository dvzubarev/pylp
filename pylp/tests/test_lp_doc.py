#!/usr/bin/env python3

from pylp.common import PosTag
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
    phrase1 = Phrase()
    phrase1.set_sent_pos_list([0, 2])
    phrase1.set_words(['t', 'p'])
    phrase2 = Phrase()
    phrase2.set_sent_pos_list([2, 3])
    phrase1.set_words(['p', 'o'])

    phrases = [phrase1, phrase2]

    sent = lp_doc.Sent(words, phrases)
    sent.filter_words([filter1])

    assert len(sent) == 2
    adjusted_phrases = list(sent.phrases())
    assert len(adjusted_phrases) == 1
    assert adjusted_phrases[0].get_sent_pos_list() == [0, 1]
