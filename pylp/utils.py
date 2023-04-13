#!/usr/bin/env python
# coding: utf-8

from typing import List

import libpyexbase

from pylp import common
from pylp.word_obj import WordObj

# * Word id functions


def word_id_combiner(words) -> int:
    w = words[0]
    for i in range(1, len(words)):
        w = libpyexbase.combine_word_id(w, words[i])
    return w


# * Syntax helpers
def adjust_syntax_links(new_sent: List[WordObj], new_positions: List[int]):
    """Example:
    old_sent: ['word', ',', 'word2', ':', 'word3']
    new_sent: ['word', 'word2', 'word3']
    new_positions: [0, -1, 1, -1, 2]

    word links with word2
    word2 links with word3
    """
    # some sanity checks
    assert len(new_positions) >= len(
        new_sent
    ), f"len of new_positions < len of new-sent: {len(new_positions)}>{len(new_sent)}"
    max_idx_val = max(new_positions)
    assert max_idx_val < len(
        new_sent
    ), f"Max val in new_positions ({max_idx_val}) > len(new_sent) {len(new_sent)}"

    for old_pos, new_pos in enumerate(new_positions):
        if new_pos == -1:
            # this word does not exist anymore
            continue

        old_parent_offs = new_sent[new_pos].parent_offs
        if old_parent_offs is None or old_parent_offs == 0:
            # this is root or no link
            continue
        old_parent_pos = old_pos + old_parent_offs

        new_parent_pos = new_positions[old_parent_pos]
        if new_parent_pos == -1:
            # parent does not exist
            new_sent[new_pos].parent_offs = 0
            new_sent[new_pos].synt_link = common.SyntLink.ORPHAN
        else:
            new_sent[new_pos].parent_offs = new_parent_pos - new_pos
