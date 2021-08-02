import logging
from io import StringIO

# Vendored from isanlp
# https://github.com/IINemo/isanlp


class Span:
    """Basic class for span-type annotations in text.

    Class members:
        begin - span offset begin.
        end - span offset end.

    """

    def __init__(self, begin=-1, end=-1):
        self.begin = begin
        self.end = end

    def left_overlap(self, other):
        """Checks whether the current span overlaps with other span on the left side."""

        return (
            self.begin <= other.begin
            and self.end <= other.end
            and self.end > other.begin
            or self.begin >= other.begin
            and self.end <= other.end
        )

    def overlap(self, other):
        """Checks whether the current span oeverlaps with other span."""

        return self.left_overlap(other) or other.left_overlap(self)

    def __str__(self):
        return '<{}, {}>'.format(self.begin, self.end)

    def __eq__(self, other):
        return self.begin == other.begin and self.end == other.end


class Token(Span):
    """Token class that expands span with its text representation in text."""

    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text


class Sentence:
    """Sentence specified by starting token number and ending token number."""

    def __init__(self, begin, end):
        self.begin = begin
        self.end = end


class WordSynt:
    """Node in syntax dependency tree."""

    def __init__(self, parent, link_name):
        self.parent = parent
        self.link_name = link_name


class ConllFormatSentenceParser:
    """Parses annotations of a single sentence in CONLL-X format aquired from stream."""

    def __init__(self, string_io):
        self.string_ = string_io
        self.stop_ = False

    def __iter__(self):
        return self

    def __next__(self):
        if not self.stop_:
            line = self.string_.readline().rstrip('\n')
            if not line:
                self.stop_ = True
            else:
                return line.strip().split('\t')

        raise StopIteration()


class ConllFormatStreamParser:
    """Parses annotations of a text document in CONLL-X format aquired from stream."""

    def __init__(self, string):
        self.string_io_ = StringIO(string)
        self.stop_ = False

    def __iter__(self):
        return self

    def __next__(self):
        if not self.stop_:
            sent_parser = ConllFormatSentenceParser(self.string_io_)
            result = list(sent_parser)
            if not result:
                self.stop_ = True
            else:
                return result
        raise StopIteration()


class ConverterConllUDV1:
    FORM = 1
    LEMMA = 2
    POSTAG = 3
    MORPH = 5
    HEAD = 6
    DEPREL = 7

    def __call__(self, conll_raw_text):
        """Performs conll text parsing.

        Args:
            text(str): text.

        Returns:
            Dictionary that contains:
            1. form - list of lists with forms of words.
            2. lemma - list of lists of strings that represent lemmas of words.
            3. postag - list of lists of strings that represent postags of words.
            4. morph - list of lists of strings that represent morphological features.
            5. syntax_dep_tree - list of lists of objects WordSynt that represent a dependency tree
        """

        try:
            result_form = []
            result_lemma = []
            result_postag = []
            result_morph = []
            result_synt = []

            for sent in ConllFormatStreamParser(conll_raw_text):
                new_sent_form = []
                new_sent_lemma = []
                new_sent_postag = []
                new_sent_morph = []
                new_sent_synt = []

                for word in sent:
                    if word[0][0] != '#':
                        new_sent_form.append(word[self.FORM])
                        new_sent_lemma.append(word[self.LEMMA])
                        new_sent_postag.append(word[self.POSTAG])
                        new_sent_morph.append(self._parse_morphology(word[self.MORPH]))
                        new_sent_synt.append(
                            self._parse_synt_tree(word[self.HEAD], word[self.DEPREL])
                        )

                result_form.append(new_sent_form)
                result_lemma.append(new_sent_lemma)
                result_postag.append(new_sent_postag)
                result_morph.append(new_sent_morph)
                result_synt.append(new_sent_synt)

        except IndexError as err:
            logging.error('Err: Index error: %s', err)
            logging.error('--------------------------------')
            logging.error(conll_raw_text)
            logging.error('--------------------------------')
            raise

        return {
            'form': result_form,
            'lemma': result_lemma,
            'postag': result_postag,
            'morph': result_morph,
            'syntax_dep_tree': result_synt,
        }

    def get_tokens(self, text, form_annotation):
        """Performs sentence splitting.

        Args:
            form_annotation(list): list of lists of forms of words.

        Returns:
            List of objects Token.
        """

        ann_tokens = list()
        prev = 0
        for sent in form_annotation:
            for form in sent:
                begin = text.find(form, prev)
                end = begin + len(form)
                ann_tokens.append(Token(text=form, begin=begin, end=end))
                prev = end

        return ann_tokens

    def sentence_split(self, form_annotation):
        """Performs sentence splitting.

        Args:
            form_annotation(list): list of lists of forms of words.

        Returns:
            List of objects Sentence.
        """

        sentences = list()
        start = 0
        for sent in form_annotation:
            sentences.append(Sentence(begin=start, end=start + len(sent)))
            start += len(sent)

        return sentences

    def _parse_morphology(self, string):
        result = [(s.split('=')) for s in string.split('|') if len(string) > 2]
        return {feature[0]: feature[1] for feature in result}

    def _parse_synt_tree(self, head, deprel):
        if head == '_':
            return None
        return WordSynt(parent=int(head) - 1, link_name=deprel)
