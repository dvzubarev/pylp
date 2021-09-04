#!/usr/bin/env python
# coding: utf-8

import copy
import logging
import unittest

from pylp.phrases.builder import build_trees
from pylp.phrases.builder import build_words
from pylp.phrases.builder import build_phrases_iter
from pylp.phrases.builder import build_phrases_recurs

from pylp.phrases.builder import NormPhrase
from pylp.phrases.builder import PhraseMerger
from pylp.phrases.builder import create_sents_with_phrases


class PhrasesTestCase(unittest.TestCase):
    def setUp(self):
        # self.phrases_builder = build_phrases_recurs
        self.phrases_builder = build_phrases_iter
        words = [
            'известный',
            '43',
            'клинический',
            'случай',
            'психоаналитический',
            'практика',
            'зигмунд',
            'фрейд',
            'весь',
            'этот',
            'работа',
        ]
        self.sent = {
            'words': words,
            'phrases': [[2, 3], [4, 5], [6, 7], [7, 5]],
            'extra': [None] * len(words),
        }

        words = ['m1', 'm2', 'r', 'm3', 'h1', 'm4', 'm5', 'h2']
        self.complex_sent = {
            'words': words,
            'phrases': [[0, 2], [1, 2], [3, 4], [4, 2], [5, 7], [6, 7], [7, 4]],
            'extra': [None] * len(words),
        }

    def test_build_trees(self):
        trees = build_trees(self.sent)
        self.assertEqual(2, len(trees))
        self.assertEqual(3, trees[0].pos())
        self.assertEqual(5, trees[1].pos())
        self.assertEqual(2, len(trees[1]._mods))

    def test_generate_phrases(self):
        phrases = self.phrases_builder(self.sent, 2)
        self.assertEqual(4, len(phrases))
        str_phrases = [p.get_id() for p in phrases]
        str_phrases.sort()
        self.assertEqual(
            [
                'зигмунд_фрейд',
                'клинический_случай',
                'практика_фрейд',
                'психоаналитический_практика',
            ],
            str_phrases,
        )

        phrases = self.phrases_builder(self.sent, 3)
        str_phrases = [p.get_id() for p in phrases]
        str_phrases.sort()
        # print(str_phrases)
        self.assertEqual(6, len(phrases))
        self.assertEqual(
            [
                'зигмунд_фрейд',
                'клинический_случай',
                'практика_зигмунд_фрейд',
                'практика_фрейд',
                'психоаналитический_практика',
                'психоаналитический_практика_фрейд',
            ],
            str_phrases,
        )

        phrases = self.phrases_builder(self.sent, 4)
        str_phrases = [p.get_id() for p in phrases]
        str_phrases.sort()
        # print(str_phrases)
        self.assertEqual(7, len(phrases))
        self.assertEqual(
            [
                'зигмунд_фрейд',
                'клинический_случай',
                'практика_зигмунд_фрейд',
                'практика_фрейд',
                'психоаналитический_практика',
                'психоаналитический_практика_зигмунд_фрейд',
                'психоаналитический_практика_фрейд',
            ],
            str_phrases,
        )

    def test_generate_complex_phrarses(self):
        phrases = self.phrases_builder(self.complex_sent, 3)

        str_phrases = [p.get_id() for p in phrases]
        str_phrases.sort()
        # print(str_phrases)
        self.assertEqual(16, len(phrases))
        etal_phrases = [
            'h1_h2',
            'h1_m4_h2',
            'h1_m5_h2',
            'm1_m2_r',
            'm1_r',
            'm1_r_h1',
            'm2_r',
            'm2_r_h1',
            'm3_h1',
            'm3_h1_h2',
            'm4_h2',
            'm4_m5_h2',
            'm5_h2',
            'r_h1',
            'r_h1_h2',
            'r_m3_h1',
        ]
        self.assertEqual(etal_phrases, str_phrases)

        phrases = self.phrases_builder(self.complex_sent, 4)

        str_phrases = [p.get_id() for p in phrases]
        str_phrases.sort()
        # print(str_phrases)
        self.assertEqual(27, len(phrases))
        etal_phrases.extend(
            [
                'm1_r_h1_h2',
                'm1_r_m3_h1',
                'm1_m2_r_h1',
                'm2_r_h1_h2',
                'm2_r_m3_h1',
                'r_h1_m4_h2',
                'r_h1_m5_h2',
                'r_m3_h1_h2',
                'h1_m4_m5_h2',
                'm3_h1_m4_h2',
                'm3_h1_m5_h2',
            ]
        )
        etal_phrases.sort()
        self.assertEqual(etal_phrases, str_phrases)

    def test_multiple_right_mods(self):
        sent = {
            'words': ['r', 'm1', 'h1', 'h2'],
            'phrases': [[2, 0], [1, 2], [3, 0]],
            'extra': [None, None, None, None],
        }

        phrases = self.phrases_builder(sent, 4)
        str_phrases = [p.get_id() for p in phrases]
        str_phrases.sort()
        # print (str_phrases)
        self.assertEqual(6, len(str_phrases))
        self.assertEqual(['m1_h1', 'r_h1', 'r_h1_h2', 'r_h2', 'r_m1_h1', 'r_m1_h1_h2'], str_phrases)

    def test_convert_phrase(self):
        # 'words': ['известный', '43', 'клинический', 'случай', 'психоаналитический',
        #           'практика', 'зигмунд', 'фрейд', 'весь', 'этот', 'работа'],
        all_words = build_words(self.sent)
        words = [all_words[4], all_words[5], all_words[6], all_words[7]]

        p = NormPhrase(words)
        self.assertEqual(4, len(p.get_words()))
        self.assertEqual(['психоаналитический', 'практика', 'зигмунд', 'фрейд'], p.get_words())

        self.assertEqual(4, len(p.get_deps()))
        self.assertEqual([1, None, 3, 1], p.get_deps())

        self.assertEqual('психоаналитический_практика_зигмунд_фрейд', p.get_id())

        words2 = [all_words[6], all_words[7]]
        p2 = NormPhrase(words2)
        self.assertEqual(2, len(p2.get_words()))
        self.assertEqual([1, None], p2.get_deps())
        self.assertEqual('зигмунд_фрейд', p2.get_id())

    def test_mods_order_phrase(self):
        sent1 = {'words': ['m1', 'm2', 'h1'], 'phrases': [[0, 2], [1, 2]]}

        sent2 = {'words': ['m2', 'm1', 'h1'], 'phrases': [[0, 2], [1, 2]]}

        words1 = build_words(sent1)
        words2 = build_words(sent2)

        phrase1 = NormPhrase(words1)
        phrase2 = NormPhrase(words2)
        self.assertEqual(phrase1.get_id(), phrase2.get_id())

    def test_phrase_merging1(self):
        words = ['m1', 'r', 'm2', 'h1']
        root = PhraseMerger(1, words)

        mod1 = PhraseMerger(0, words)

        root = root.make_new_phrase(mod1, words)

        self.assertEqual(2, len(root.get_words()))
        self.assertEqual(['m1', 'r'], root.get_words())
        self.assertEqual([1, None], root.get_deps())
        self.assertEqual('m1_r', root.get_id())

        root_m1_r = copy.deepcopy(root)

        head1 = PhraseMerger(3, words)
        root = root.make_new_phrase(head1, words)
        self.assertEqual(3, len(root.get_words()))
        self.assertEqual(['m1', 'r', 'h1'], root.get_words())
        self.assertEqual([1, None, -1], root.get_deps())
        self.assertEqual('m1_r_h1', root.get_id())

        root = copy.deepcopy(root_m1_r)
        mod2 = PhraseMerger(2, words)
        head1 = head1.make_new_phrase(mod2, words)
        root = root.make_new_phrase(head1, words)
        self.assertEqual(4, len(root.get_words()))
        self.assertEqual(['m1', 'r', 'm2', 'h1'], root.get_words())
        self.assertEqual([1, None, 1, -2], root.get_deps())
        self.assertEqual('m1_r_m2_h1', root.get_id())

        words = ['r', 'm1', 'h1', 'h2']
        root = PhraseMerger.mod_head2phrase(3, 0, words)
        mod = PhraseMerger.mod_head2phrase(1, 2, words)
        root = root.make_new_phrase(mod, words)
        self.assertEqual(4, len(root.get_words()))
        self.assertEqual(['r', 'm1', 'h1', 'h2'], root.get_words())
        self.assertEqual([None, 1, -2, -3], root.get_deps())
        self.assertEqual('r_m1_h1_h2', root.get_id())

        words = ['m1', 'm2', 'r']
        root = PhraseMerger.mod_head2phrase(0, 2, words)
        mod = PhraseMerger(1, words)
        root = root.make_new_phrase(mod, words)
        self.assertEqual(3, len(root.get_words()))
        self.assertEqual(['m1', 'm2', 'r'], root.get_words())
        self.assertEqual([2, 1, None], root.get_deps())
        self.assertEqual('m1_m2_r', root.get_id())

    def test_replace(self):
        sent = {
            'words': ['r', 'm1', 'h1', 'h2'],
            'phrases': [[2, 0], [1, 2], [3, 0]],
            'extra': [None, None, None, None],
        }

        new_sent = create_sents_with_phrases([sent], 3, '_'.join, create_mode='replace')[0]

        print(new_sent)
        self.assertEqual(2, len(new_sent))

        str_phrases = [p['id'] for p in new_sent]
        str_phrases.sort()
        self.assertEqual(['r_h1_h2', 'r_m1_h1'], str_phrases)
