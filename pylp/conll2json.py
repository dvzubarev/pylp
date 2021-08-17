#!/usr/bin/env python
# coding: utf-8

from pylp.converter_conll_ud_v1 import ConverterConllUDV1
from pylp.isanlp_converter import convert_to_json


class _SplitTokensIntoSents:
    """Extra processor for easy converting to json."""

    def __call__(self, tokens, sents):
        result_tokens_list = []
        for sent in sents:
            result_tokens_list.append(
                [(t.begin, t.end - t.begin) for t in tokens[sent.begin : sent.end]]
            )

        return {'tokens': result_tokens_list}


class _MergePostagIntoMorph:
    def __call__(self, postag, morph):
        if morph:
            if morph[0]:
                if 'fPOS' in morph[0][0]:
                    return {'morph': morph}

        for sent_postag, sent_morph in zip(postag, morph):
            for PoS, morph_feats in zip(sent_postag, sent_morph):
                morph_feats['fPOS'] = PoS

        return {'morph': morph}


def _from_conll(text, conll_annots):
    converter = ConverterConllUDV1()
    annotations = converter(conll_annots)

    for sent_lemma in annotations['lemma']:
        for i in range(len(sent_lemma)):
            sent_lemma[i] = sent_lemma[i].lower()

    annotations['sentences'] = converter.sentence_split(annotations['form'])
    annotations['tokens'] = converter.get_tokens(text, annotations['form'])

    p1 = _SplitTokensIntoSents()
    annotations['tokens'] = p1(annotations['tokens'], annotations['sentences'])['tokens']
    p2 = _MergePostagIntoMorph()
    annotations['morph'] = p2(annotations['postag'], annotations['morph'])['morph']

    return annotations


def convert(text, conll_annots, lang, analyze_opts: dict = None):
    # TODO Its legacy code
    # Need to simplify and get rid of unnecessary convertation to isanlp annotations

    annots = _from_conll(text, conll_annots)
    annots['lang'] = lang
    result, _ = convert_to_json(
        annots,
        calc_stat=False,
        analyze_opts=analyze_opts,
    )
    return result
