#!/usr/bin/env python
# coding: utf-8

from ex_pylp.utils import make_words_dict
from ex_pylp.common import Attr
import ex_pylp.converter as conv


###Annotations convertors

class LemmaConv:
    def __init__(self, lemmas_dict):
        self._lemmas_dict = lemmas_dict

    def __call__(self, pos, lemma):
        return [(Attr.WORD_NUM, self._lemmas_dict[lemma])]

class SyntConv(conv.SyntConv):
    def __call__(self, pos, word_synt):
        return super(SyntConv, self).__call__(pos, word_synt.parent, word_synt.link_name)

class MorphConv(conv.MorphConv):
    def __call__(self, pos, morph_feats):
        tag = morph_feats.get('fPOS', '')
        return super(MorphConv, self).__call__(pos, tag, morph_feats)


class TokensConv:
    def __call__(self, pos, offs_and_len):
        offs, size = offs_and_len
        return [(Attr.OFFSET, offs), (Attr.LENGTH, size)]



def convert_to_json(annotations, calc_stat = False):
    result = {}
    result['lang'] = conv.convert_lang(annotations['lang'])

    flatten_lemmas, lemmas_dict = make_words_dict(annotations['lemma'])
    result['words'] = flatten_lemmas

    converters = [
        ('lemma', LemmaConv(lemmas_dict)),
        ('syntax_dep_tree', SyntConv(calc_stat = calc_stat)),
        ('morph', MorphConv(calc_stat = calc_stat)),
        ('tokens', TokensConv())
    ]
    all_facets = [annotations[item[0]] for item in converters]

    #TODO check that sents have the same size for all facets
    sents = []
    for facets_by_sent in zip(*all_facets):
        sent = []
        for word_pos, facets in enumerate(zip(*facets_by_sent)):
            word_obj = {}
            for num, val in enumerate(facets):
                t = converters[num][1](word_pos, val)
                if t:
                    word_obj.update(t)
            sent.append(word_obj)
        sents.append(sent)

    result['sents'] = sents

    stats = {conv_item[0] : conv_item[1].stat() for conv_item in converters
             if hasattr(conv_item[1], 'stat')}
    return result, stats
