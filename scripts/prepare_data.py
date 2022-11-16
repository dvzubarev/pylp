#!/usr/bin/env python3


import argparse
import logging
import urllib.request
import os
import collections
import json
import gzip

from pylp.phrases.inflect import VerbExcpForms

EN_LEMMA_EXCEP_URL = 'https://raw.githubusercontent.com/explosion/spacy-lookups-data/master/spacy_lookups_data/data/en_lemma_exc.json'

WELL_KNOWN_PLURAL_WITHOUT_S_SUFFIX = frozenset(
    [
        'addenda',
        'alumnae',
        'alumni',
        'antennae',
        'bacilli',
        'bacteria',
        'beaux',
        'bureaux',
        'cacti',
        'chateaux',
        'children',
        'concerti',
        'corpora',
        'criteria',
        'curricula',
        'errata',
        'foci',
        'feet',
        'formulae',
        'fungi',
        'genera',
        'geese',
        'graffiti',
        'larvae',
        'libretti',
        'loci',
        'lice',
        'men',
        'media',
        'memoranda',
        'minutiae',
        'mice',
        'nebulae',
        'nuclei',
        'opera',
        'ova',
        'oxen',
        'phenomena',
        'phyla',
        'radii',
        'referenda',
        'stimuli',
        'strata',
        'syllabi',
        'symposia',
        'tableaux',
        'teeth',
        'vertebrae',
        'vitae',
        'women',
    ]
)

WELL_KNOWN_PAST_PART = frozenset(
    [
        'abode',
        'arisen',
        'awoken',
        'been',
        'born',
        'beaten',
        'become',
        'begotten',
        'begun',
        'bent',
        'bet',
        'bidden',
        'bitten',
        'bled',
        'blown',
        'broken',
        'brought',
        'broadcast',
        'built',
        'burnt',
        'burst',
        'bought',
        'could',
        'cast',
        'caught',
        'chid',
        'chosen',
        'clung',
        'clad',
        'come',
        'cost',
        'crept',
        'cut',
        'dealt',
        'dug',
        'dove',
        'done',
        'drawn',
        'dreamt',
        'drunk',
        'driven',
        'dwelt',
        'eaten',
        'fallen',
        'fed',
        'felt',
        'fought',
        'found',
        'fled',
        'flung',
        'flown',
        'forbidden',
        'forecast',
        'foreseen',
        'forgotten',
        'forgiven',
        'forsaken',
        'frozen',
        'got',
        'given',
        'gone',
        'ground',
        'grown',
        'hung',
        'had',
        'heard',
        'hidden',
        'hit',
        'held',
        'hurt',
        'kept',
        'knelt',
        'known',
        'laid',
        'led',
        'leant',
        'leapt',
        'learnt',
        'left',
        'lent',
        'let',
        'lain',
        'lit',
        'lost',
        'made',
        'meant',
        'met',
        'mown',
        'offset',
        'overcome',
        'partaken',
        'paid',
        'pled',
        'preset',
        'proven',
        'put',
        'quit',
        'read',
        'relaid',
        'rent',
        'rid',
        'rung',
        'risen',
        'run',
        'sawn',
        'said',
        'seen',
        'sought',
        'sold',
        'sent',
        'set',
        'shaken',
        'shed',
        'shone',
        'shod',
        'shot',
        'shown',
        'shut',
        'sung',
        'sunk',
        'sat',
        'slain',
        'slept',
        'slid',
        'slit',
        'smelt',
        'sown',
        'spoken',
        'sped',
        'spelt',
        'spent',
        'spilt',
        'spun',
        'spat',
        'split',
        'spoilt',
        'spread',
        'sprung',
        'stood',
        'stolen',
        'stuck',
        'stung',
        'stunk',
        'strewn',
        'struck',
        'striven',
        'sworn',
        'sweat',
        'swept',
        'swollen',
        'swum',
        'swung',
        'taken',
        'taught',
        'torn',
        'told',
        'thought',
        'thriven',
        'thrown',
        'thrust',
        'typeset',
        'undergone',
        'understood',
        'woken',
        'worn',
        'wept',
        'wetted',
        'won',
        'wound',
        'withdrawn',
        'wrung',
        'written',
    ]
)


def _prep_lemma_excp_data_for_noun(form_to_lemmas_dict):
    # create a dict: lemma -> plural form
    lemma_to_plur_dict = {}
    for form, lemmas in form_to_lemmas_dict.items():
        if form.endswith('s') or form in WELL_KNOWN_PLURAL_WITHOUT_S_SUFFIX:
            for l in lemmas:
                lemma_to_plur_dict[l] = form
    return lemma_to_plur_dict


def _try_hard_finding_past_part(word):
    "handle those cases: overpaid, overthrown, underbought, spoon-fed, etc"
    for i in range(3, 10):
        if i >= len(word):
            break
        suffix = word[-i:]
        if suffix in WELL_KNOWN_PAST_PART:
            return True
    return False


def _prep_lemma_excp_data_for_verb(form_to_lemmas_dict):
    # create a dict: lemma -> VerbExcpForms
    lemma_to_verb_forms_dict = collections.defaultdict(VerbExcpForms)
    for form, lemmas in form_to_lemmas_dict.items():
        if form.endswith('ing'):
            for l in lemmas:
                lemma_to_verb_forms_dict[l].pres_part = form

        if form.endswith('ed') or form in WELL_KNOWN_PAST_PART or _try_hard_finding_past_part(form):
            for l in lemmas:
                lemma_to_verb_forms_dict[l].past_part = form

    return lemma_to_verb_forms_dict


def prepare_en_inflecter_excp_data(opts):
    tmp_filename = '/tmp/en_lemma_exc.json'
    try:
        urllib.request.urlretrieve(EN_LEMMA_EXCEP_URL, tmp_filename)
        with open(tmp_filename, 'r', encoding='utf8') as f:
            obj = json.load(f)
            lemma_to_plur_dict = _prep_lemma_excp_data_for_noun(obj['noun'])
            lemma_to_verb_forms_dict = _prep_lemma_excp_data_for_verb(obj['verb'])

            excp_dict = {'noun': lemma_to_plur_dict, 'verb': lemma_to_verb_forms_dict}
            with gzip.open('pylp/phrases/data/en_lemma_exc.json.gz', 'wt', encoding='utf8') as outf:
                json.dump(excp_dict, outf, default=lambda d: d.to_json())

    finally:
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", default=False)

    subparsers = parser.add_subparsers(help='sub-command help')

    prepare_en_inflect_data_parser = subparsers.add_parser(
        'prepare_en_lemma_data', help='help of prepare_en_lemma_data'
    )

    prepare_en_inflect_data_parser.set_defaults(func=prepare_en_inflecter_excp_data)

    args = parser.parse_args()

    FORMAT = "%(asctime)s %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format=FORMAT)
    try:

        args.func(args)
    except Exception as e:
        logging.exception("failed to prepare_en_lemmatazier_excp_data: %s ", e)


if __name__ == '__main__':
    main()
