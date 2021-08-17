#!/usr/bin/env python
# coding: utf-8


from pylp.utils import make_words_dict
from pylp.common import Attr
import pylp.converter as conv


###Annotations convertors


class LemmaConv:
    def __init__(self, lemmas_dict):
        self._lemmas_dict = lemmas_dict

    def __call__(self, pos, lemma):
        return [(Attr.WORD_NUM, self._lemmas_dict[lemma])]


class SyntConv(conv.SyntConv):
    def __call__(self, pos, word_synt):
        if word_synt is not None:
            return super().__call__(pos, word_synt.parent, word_synt.link_name)
        return None


class MorphConv(conv.MorphConv):
    def __call__(self, pos, morph_feats):
        tag = morph_feats.get('fPOS', '')
        return super().__call__(pos, tag, morph_feats)


class TokensConv:
    def __call__(self, pos, offs_and_len):
        offs, size = offs_and_len
        return [(Attr.OFFSET, offs), (Attr.LENGTH, size)]


def convert_to_json(annotations, calc_stat=False, analyze_opts: dict = None):
    if analyze_opts is None:
        analyze_opts = {}
    result = {}
    result['lang'] = conv.convert_lang(annotations['lang'])

    flatten_lemmas, lemmas_dict = make_words_dict(annotations['lemma'])
    result['words'] = flatten_lemmas

    converters = [
        ('tokens', TokensConv()),
    ]
    if analyze_opts.get('tagger', '') != 'none':
        converters.extend(
            [
                ('lemma', LemmaConv(lemmas_dict)),
                ('morph', MorphConv(calc_stat=calc_stat)),
            ]
        )

    if analyze_opts.get('parser', '') != 'none':
        converters.append(
            ('syntax_dep_tree', SyntConv(calc_stat=calc_stat)),
        )

    all_facets = [annotations[item[0]] for item in converters]

    # TODO check that sents have the same size for all facets
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

    stats = {
        conv_item[0]: conv_item[1].stat()
        for conv_item in converters
        if hasattr(conv_item[1], 'stat')
    }
    return result, stats
