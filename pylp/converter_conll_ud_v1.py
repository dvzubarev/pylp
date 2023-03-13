import logging
from io import StringIO

from pylp import common
from pylp import lp_doc
from pylp.word_obj import WordObj
import pylp.phrases.builder

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


DEF_PHRASE_BUILDER_OPTS = pylp.phrases.builder.PhraseBuilderOpts()


def _assign_morph_features(word_obj: WordObj, morph_feats, pos_tag):
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

    if pos_tag == common.PosTag.VERB and 'Mood' in morph_feats:
        word_obj.mood = common.WORD_MOOD_DICT[morph_feats['Mood'].upper()]

    if 'NumType' in morph_feats:
        word_obj.num_type = common.WORD_NUM_TYPE_DICT[morph_feats['NumType'].upper()]

    if 'Animacy' in morph_feats:
        word_obj.animacy = common.WORD_ANIMACY_DICT[morph_feats['Animacy'].upper()]


def _adjust_verb(pos_tag, morph_feats):
    if 'VerbForm' in morph_feats:
        if morph_feats['VerbForm'] == 'Part':
            if 'Variant' in morph_feats and morph_feats['Variant'] == 'Short':
                return common.PosTag.PARTICIPLE_SHORT
            return common.PosTag.PARTICIPLE
        if morph_feats['VerbForm'] == 'Ger':
            return common.PosTag.GERUND
        if morph_feats['VerbForm'] == 'Conv':
            return common.PosTag.PARTICIPLE_ADVERB
    return pos_tag


def _adjust_adj(pos_tag, morph_feats):
    if 'Variant' in morph_feats and morph_feats['Variant'] == 'Short':
        return common.PosTag.ADJ_SHORT
    return pos_tag


def convert_upos_tag(conllu_pos_tag: str, morph_feats):
    if conllu_pos_tag == '_':
        return common.PosTag.UNDEF
    if conllu_pos_tag in ("''", '.', '``'):
        # trash from AmalGUM
        return common.PosTag.PUNCT
    pos_tag = common.POS_TAG_DICT.get(conllu_pos_tag, common.PosTag.UNDEF)
    if pos_tag == common.PosTag.UNDEF:
        logging.warning("Unknown conllu_pos_tag: %s", conllu_pos_tag)

    # TODO other verb forms Fin? Imp?
    # TODO 'VerbForm' may occur not only for verbs
    if pos_tag == common.PosTag.VERB:
        return _adjust_verb(pos_tag, morph_feats)
    if pos_tag == common.PosTag.ADJ:
        return _adjust_adj(pos_tag, morph_feats)

    return pos_tag


def fill_morph_info(conllu_pos_tag: str, morph_str: str, word_obj: WordObj):
    morph_feats = [(s.split('=')) for s in morph_str.split('|') if len(morph_str) > 2]
    morph_feats = dict(morph_feats)
    word_obj.pos_tag = convert_upos_tag(conllu_pos_tag, morph_feats)

    _assign_morph_features(word_obj, morph_feats, word_obj.pos_tag)


def fill_syntax_info(
    word_pos, conllu_head: int | None, conllu_deprel: str, enh_deps: str, word_obj: WordObj
):
    # TODO what to do with modificators?
    # flat:name
    # nsubj:pass
    # acl:relcl
    # cc:preconj

    head = None
    rel = None
    if enh_deps and enh_deps != '_':
        dep_vars = enh_deps.split('|')
        # choose the one that can be used to make phrases later
        for var in dep_vars:
            head_str, rel_str, *_ = var.split(':', 2)
            temp_rel = common.SYNT_LINK_DICT[rel_str.upper()]
            if (
                temp_rel == common.SyntLink.CONJ
                or temp_rel in DEF_PHRASE_BUILDER_OPTS.good_synt_rels
            ):
                rel = temp_rel
                head = int(head_str)
                break
            if head is None:
                head = int(head_str)
                rel = temp_rel

    if head is None and conllu_head is not None:
        head = conllu_head
    if rel is None and conllu_deprel and conllu_deprel != '_':
        rel = common.SYNT_LINK_DICT[conllu_deprel.split(':', 1)[0].upper()]

    if head is not None and rel is not None:
        head -= 1
        if head != -1:
            word_obj.parent_offs = head - word_pos
        else:
            word_obj.parent_offs = 0

        word_obj.synt_link = rel


class ConverterConllUDV1:
    FORM = 1
    LEMMA = 2
    POSTAG = 3
    MORPH = 5
    HEAD = 6
    DEPREL = 7
    ENH_DEP = 8

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
        # pos_tag = convert_upos_tag(word[self.POSTAG])

        lemma = word[self.LEMMA].lower()
        if lemma == '_':
            lemma = ''
        word_obj = WordObj(lemma=lemma, form=word[self.FORM])

        fill_morph_info(word[self.POSTAG], word[self.MORPH], word_obj)

        self._set_syntax(pos, word, word_obj)

        return word_obj

    def _set_syntax(self, pos: int, word: tuple, word_obj: WordObj):
        head = word[self.HEAD]
        if head == '_':
            head = None
        else:
            head = int(head)

        fill_syntax_info(pos, head, word[self.DEPREL], word[self.ENH_DEP], word_obj)
