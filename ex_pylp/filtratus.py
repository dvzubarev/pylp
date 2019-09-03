#!/usr/bin/env python
# coding: utf-8

from ex_pylp.common import Attr
from ex_pylp.common import PosTag
from ex_pylp.common import SyntLink

class Filtratus:
    """http://www.filtratus.com
    """
    def _filter(self, word_obj, word_pos, sent, word_strings):
        raise NotImplementedError ("!")

    def _adjust_syntax_links(self, new_sent, old_sent, new_positions):
        """Example:
        old_sent: ['word', ',', 'word2', ':', 'word3']
        new_sent: ['word', 'word2', 'word3']
        new_positions: [0, -1, 1, -1, 2]

        word links with word2
        word2 links with word3
        """
        for old_pos, old_word in enumerate(old_sent):
            if new_positions[old_pos] == -1:
                #this word does not exist anymore
                continue
            new_pos = new_positions[old_pos]

            old_parent_offs = new_sent[new_pos].get(Attr.SYNTAX_PARENT, -1)
            if old_parent_offs == -1:
                #this is root or no link
                continue
            old_parent_pos = old_pos + old_parent_offs

            new_parent_pos = new_positions[old_parent_pos]
            if new_parent_pos == -1:
                #parent does not exist
                if Attr.SYNTAX_LINK_NAME in new_sent[new_pos]:
                    del new_sent[new_pos][Attr.SYNTAX_LINK_NAME]
                if Attr.SYNTAX_PARENT in new_sent[new_pos]:
                    del new_sent[new_pos][Attr.SYNTAX_PARENT]

            else:
                new_sent[new_pos][Attr.SYNTAX_PARENT] = new_parent_pos - new_pos





    def __call__(self, doc_obj):
        new_sents = []
        for sent in doc_obj['sents']:
            new_sent = []
            new_positions = []
            cur_pos = 0
            for word_pos, word_obj in enumerate(sent):
                if self._filter(word_obj, word_pos, sent, doc_obj['words']):
                    new_positions.append(-1)
                else:
                    new_sent.append(word_obj)
                    new_positions.append(cur_pos)
                    cur_pos += 1
            if len(new_sent) != len(sent):
                self._adjust_syntax_links(new_sent, sent, new_positions)
            new_sents.append(new_sent)
        doc_obj['sents'] = new_sents
        #TODO remove unused words from doc_obj['words']


class PunctAndUndefFiltratus(Filtratus):
    def _filter(self, word_obj, word_pos, sent, word_strings):
        if word_obj.get(Attr.POS_TAG, PosTag.UNDEF) in (PosTag.UNDEF, PosTag.PUNCT) and \
           word_obj.get(Attr.SYNTAX_LINK_NAME, SyntLink.PUNCT) == SyntLink.PUNCT:
            return True
        return False

class DeterminatusFiltratus(PunctAndUndefFiltratus):
    def _filter(self, word_obj, word_pos, sent, word_strings):
        filtered = super(DeterminatusFiltratus, self)._filter(word_obj, word_pos,
                                                              sent, word_strings)
        if filtered:
            return True
        if word_obj[Attr.POS_TAG] == PosTag.DET:
            return True
        return False

class StopWordsFiltratus(PunctAndUndefFiltratus):
    def _filter(self, word_obj, word_pos, sent, word_strings):
        filtered = super(StopWordsFiltratus, self)._filter(word_obj, word_pos, sent, word_strings)
        if filtered:
            return True
        #TODO filter CONJ with link cc ?
        #TODO filter words with links case, obl, fixed, mark, det?


def create_filtratus():
    #TODO factory
    return DeterminatusFiltratus()
