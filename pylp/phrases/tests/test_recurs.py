#!/usr/bin/env python
# coding: utf-8

import unittest

from pylp.phrases.recurs import build_trees, build_words, NormPhrase


class PhrasesTestCase(unittest.TestCase):
    def setUp(self):
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
        sent = []
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
