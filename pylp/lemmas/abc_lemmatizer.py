#!/usr/bin/env python3


from typing import List, Tuple

from pylp import lp_doc
from pylp.word_obj import WordObj


class AbcLemmatizer:
    def produce_lemma(
        self, word_obj: WordObj, lemmas_freq_list: List[Tuple[str, int]] | None = None
    ) -> str | None:
        raise NotImplementedError("produce_lemma")

    def __call__(self, doc_obj: lp_doc.Doc):
        raise NotImplementedError("__call__")
