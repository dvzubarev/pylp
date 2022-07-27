import logging
from io import StringIO

from pylp import common
from pylp import lp_doc
from pylp.word_obj import WordObj

# inspired by the code from isanlp
# https://github.com/IINemo/isanlp


class ConllFormatStreamParser:
    """Parses annotations of a text document in CONLL-X format aquired from stream."""

    def __init__(self, string):
        self._string_io = StringIO(string)

    def __iter__(self):
        sent = []
        for l in self._string_io:
            l = l.strip()
            if not l:
                if sent:
                    yield sent
                sent = []
            else:
                sent.append(l.split('\t'))


class ConverterConllUDV1:
    FORM = 1
    LEMMA = 2
    POSTAG = 3
    MORPH = 5
    HEAD = 6
    DEPREL = 7

    def __call__(self, text, conll_raw_text, doc: lp_doc.Doc) -> lp_doc.Doc:
        """Performs conll text parsing.

        Args:
            text(str): text.

        Returns:
        lp_doc.Doc
        """
        cur_text_pos = 0
        try:
            for conllu_sent in ConllFormatStreamParser(conll_raw_text):

                sent = lp_doc.Sent()

                for word in conllu_sent:
                    if word[0].startswith('#'):
                        continue
                    word_obj = self._create_word_obj(len(sent), word)

                    # set offsets of a word in the text
                    begin = text.find(word_obj.form, cur_text_pos)
                    if begin == -1:
                        raise RuntimeError(
                            f"Failed to find form {word_obj.form} in text: {text[cur_text_pos: 50]}"
                        )
                    word_obj.offset = begin
                    assert word_obj.form is not None, "not initialized form"
                    word_obj.len = len(word_obj.form)
                    cur_text_pos = begin + word_obj.len

                    sent.add_word(word_obj)
                doc.add_sent(sent)

        except IndexError as err:
            logging.error('Err: Index error: %s', err)
            logging.error('--------------------------------')
            logging.error(conll_raw_text)
            logging.error('--------------------------------')
            raise

        return doc

    def _create_word_obj(self, pos, word):
        ud_tag = word[self.POSTAG]
        if ud_tag == '_':
            pos_tag = common.PosTag.UNDEF
        else:
            pos_tag = common.POS_TAG_DICT[ud_tag]

        lemma = word[self.LEMMA].lower()
        if lemma == '_':
            lemma = ''
        word_obj = WordObj(lemma=lemma, form=word[self.FORM], pos_tag=pos_tag)

        morph_str = word[self.MORPH]
        morph_feats = [(s.split('=')) for s in morph_str.split('|') if len(morph_str) > 2]
        morph_feats = dict(morph_feats)

        # TODO verb moods? other verb forms Fin? Imp?
        # TODO 'VerbForm' may occur not only for verbs
        if pos_tag == common.PosTag.VERB:
            self._adjust_verb(morph_feats, word_obj)
        elif pos_tag == common.PosTag.ADJ:
            self._adjust_adj(morph_feats, word_obj)

        self._assign_morph_features(word_obj, morph_feats)

        if word[self.HEAD] != '_':
            parent_pos = int(word[self.HEAD]) - 1
            if parent_pos != -1:
                word_obj.parent_offs = parent_pos - pos
            else:
                word_obj.parent_offs = 0

            # TODO what to do with modificators?
            # nsubj:pass
            # acl:relcl
            # cc:preconj
            n = common.SYNT_LINK_DICT[word[self.DEPREL].split(':', 1)[0].upper()]
            word_obj.synt_link = n

        return word_obj

    def _adjust_verb(self, morph_feats, word_obj: WordObj):
        if 'VerbForm' in morph_feats:
            if morph_feats['VerbForm'] == 'Part':
                if 'Variant' in morph_feats and morph_feats['Variant'] == 'Short':
                    word_obj.pos_tag = common.PosTag.PARTICIPLE_SHORT
                else:
                    word_obj.pos_tag = common.PosTag.PARTICIPLE
            elif morph_feats['VerbForm'] in ('Ger', 'Conv'):
                word_obj.pos_tag = common.PosTag.PARTICIPLE_ADVERB

    def _adjust_adj(self, morph_feats, word_obj: WordObj):
        if 'Variant' in morph_feats and morph_feats['Variant'] == 'Short':
            word_obj.pos_tag = common.PosTag.ADJ_SHORT

    def _assign_morph_features(self, word_obj: WordObj, morph_feats):
        if 'Number' in morph_feats:
            word_obj.number = common.WORD_NUMBER_DICT[morph_feats['Number'].upper()]
        if 'Gender' in morph_feats:
            word_obj.gender = common.WORD_GENDER_DICT[morph_feats['Gender'].upper()]

        if 'Case' in morph_feats:
            word_obj.case = common.WORD_CASE_DICT[morph_feats['Case'].upper()]

        if 'Tense' in morph_feats:
            word_obj.tense = common.WORD_TENSE_DICT[morph_feats['Tense'].upper()]

        if 'Person' in morph_feats:
            word_obj.person = common.WORD_PERSON_DICT[morph_feats['Person'].upper()]

        if 'Degree' in morph_feats:
            word_obj.degree = common.WORD_DEGREE_DICT[morph_feats['Degree'].upper()]

        if 'Aspect' in morph_feats:
            word_obj.aspect = common.WORD_ASPECT_DICT[morph_feats['Aspect'].upper()]

        if 'Voice' in morph_feats:
            word_obj.voice = common.WORD_VOICE_DICT[morph_feats['Voice'].upper()]

        if 'Animacy' in morph_feats:
            word_obj.animacy = common.WORD_ANIMACY_DICT[morph_feats['Animacy'].upper()]
        # TODO valency?
