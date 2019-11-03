from typing import Dict, List

import markovify
import nltk
import spacy
from cytoolz.functoolz import pipe
from nltk.corpus import brown
from nltk.corpus import wordnet as wn
from textacy.preprocessing import (normalize_hyphenated_words,
                                   normalize_quotation_marks,
                                   normalize_unicode, normalize_whitespace)
from tracery import Grammar
from tracery.modifiers import base_english

nltk.download('brown')
nltk.download('gutenberg')
nlp = spacy.load('en_core_web_lg')


class POSifiedText(markovify.Text):
    separator = "::"

    def __init__(self, input_text, state_size=2, chain=None,
                 parsed_sentences=None, well_formed=True, reject_reg=''):
        self.synonyms: Dict[str, List[str]] = {}

        self.pos_converter = {
            "ADJ": wn.ADJ,
            "ADV": wn.ADV,
            "NOUN": wn.NOUN,
            "VERB": wn.VERB
        }

        input_text = pipe(
            input_text,
            normalize_hyphenated_words,
            normalize_quotation_marks,
            normalize_unicode,
            normalize_whitespace
        )

        markovify.Text.__init__(self, input_text, state_size, chain,
                                parsed_sentences, False,
                                well_formed, reject_reg)

        self.grammar = Grammar(self.synonyms)
        self.grammar.add_modifiers(base_english)

    def sentence_join(self, sentences):
        return " ".join(sentences)

    def word_split(self, sentence):
        tokenized = []
        first = True

        for word in nlp(sentence):
            default = True
            if word.pos_ in self.pos_converter:
                syns = wn.synsets(word.orth_, self.pos_converter[word.pos_])

                default = len(syns) == 0
                if not default:
                    modifiers = []

                    syn = syns[0]
                    name = syn.name().replace('.', '<>')

                    if first:
                        modifiers.append('.capitalize')

                    tokenized.append(self.separator.join(('#{}{}#'.format(
                        name, ''.join(modifiers)), word.tag_)))

                    if name not in self.synonyms:
                        self.synonyms[name] = [l.name() for l in syn.lemmas()]

            if default:
                tokenized.append(self.separator.join((word.orth_, word.tag_)))

            first = False

        return tokenized

    def word_join(self, words):
        sentence = " ".join(word.split(self.separator)[0] for word in words)
        return self.grammar.flatten(sentence)


# corpus = "\n".join([gt.raw(fileid) for fileid in gt.fileids()])
corpus = '\n'.join([' '.join(s) for s in brown.sents()])

bot = POSifiedText(corpus)

for _ in range(10):
    print(bot.make_sentence())
