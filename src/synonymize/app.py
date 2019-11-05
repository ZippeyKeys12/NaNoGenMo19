import re
from collections import defaultdict
from typing import Dict, List

import markovify
import nltk
import numpy as np
import spacy
from cytoolz.functoolz import pipe
from lemminflect import getInflection
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import Synset
from textacy.preprocessing import (normalize_hyphenated_words,
                                   normalize_quotation_marks,
                                   normalize_unicode, normalize_whitespace)
from tracery import Grammar
from tracery.modifiers import base_english

from ..util import PENN_TO_UNIVERSAL

nltk.download('brown')
nltk.download('gutenberg')
nlp = spacy.load('en_core_web_lg')
word2vec = spacy.load('en_vectors_web_lg')


class POSifiedText(markovify.Text):
    separator = "::"
    clean_pattern = re.compile('[\n_]')
    tracery_pattern = re.compile('^#.+#$')

    def __init__(self, input_text, state_size=2, chain=None,
                 parsed_sentences=None, well_formed=True, reject_reg=''):
        self.synonyms: Dict[str, List[str]] = defaultdict(list)
        self.entities: Dict[str, List[str]] = defaultdict(list)

        self.pos_converter = {
            "ADJ": wn.ADJ,
            "ADV": wn.ADV,
            "NOUN": wn.NOUN,
            "VERB": wn.VERB
        }

        input_text = pipe(
            input_text,
            # lambda x: x.replace('\n', ' '),
            lambda x: self.clean_pattern.sub(' ', x),
            normalize_hyphenated_words,
            normalize_quotation_marks,
            normalize_unicode,
            normalize_whitespace
        )

        markovify.Text.__init__(self, input_text, state_size, chain,
                                parsed_sentences, False,
                                well_formed, reject_reg)

        self.grammar = Grammar({**self.synonyms, **self.entities})
        self.grammar.add_modifiers(base_english)

    def sentence_join(self, sentences):
        return " ".join(sentences)

    def word_split(self, sentence):
        tokenized = []
        first = True
        entity = False

        entity_construct = {"tag": "", "type": "", "words": []}
        for word in nlp(sentence):
            default = True

            if word.ent_iob_ == "B":
                entity = True
                entity_construct['tag'] = word.tag_
                entity_construct['type'] = word.ent_type_
                entity_construct['words'] = []
            elif entity and word.ent_iob_ == 'O':
                entity = False
                text = self.separator.join((" ".join(
                    entity_construct['words']), entity_construct['tag']))

                tokenized.append(text)
                self.entities[entity_construct['type']].append(text)

            if word.pos_ in self.pos_converter:
                syns = wn.synsets(word.orth_, self.pos_converter[word.pos_])

                default = len(syns) == 0
                if not default:
                    modifiers = []

                    syn = self.get_best_synset(word.orth_, syns)
                    name = syn.name().replace('.', '<>')

                    if (not (first or entity) and
                            tokenized[-1].lower() in {'a', 'an'}):
                        if tokenized[-1] != tokenized[-1].lower():
                            first = True
                        modifiers.append('.a')

                    if first or entity:
                        modifiers.append('.capitalize')

                    if entity:
                        text = '#{}{}#'.format(name, ''.join(modifiers))
                    else:
                        text = self.separator.join(('#{}{}#'.format(
                            name, ''.join(modifiers)), word.tag_))

                    if name not in self.synonyms:
                        self.synonyms[name] = [l.name() for l in syn.lemmas()]

            if default:
                if entity:
                    text = word.orth_
                else:
                    text = self.separator.join((word.orth_, word.tag_))

            if entity:
                entity_construct['words'].append(text)
            else:
                tokenized.append(text)

            first = False

        return tokenized

    def word_join(self, words):
        sentence = []
        for word in words:
            print(word)
            (word, tag) = word.split(self.separator)

            if (self.tracery_pattern.match(word) and
                    PENN_TO_UNIVERSAL[tag] == 'VERB'):
                word = self.grammar.flatten(word).split('_')

                # TODO: Make more intelligent
                inflection = getInflection(word[0], tag)

                if len(inflection) > 0:
                    word[0] = inflection[0]

                sentence.append(' '.join(word))
            else:
                sentence.append(self.grammar.flatten(word))

        return " ".join(sentence).replace('_', ' ')

    def get_best_synset(self, word: str, syns: List[Synset]) -> str:
        word_token = word2vec(word)

        best = {
            'name': '',
            'val': None
        }

        if not np.count_nonzero(word_token.vector):
            return syns[0]

        for syn in syns:
            name = syn.name()

            lemma = None
            for l in syn.lemmas():
                if '_' not in l.name():
                    lemma = l.name().lower()
                    token = word2vec(lemma)

                    if not np.count_nonzero(token.vector):
                        if best['name'] == '':
                            best['name'] = name

                        continue

                    val = word_token.similarity(token)

                    if best['val'] is None or val > best['val']:
                        best['name'] = name
                        best['val'] = val

        return wn.synset(best['name'])


def main():
    # corpus = "\n".join([gt.raw(fileid) for fileid in gt.fileids()])
    # corpus = '\n'.join([' '.join(s) for s in brown.sents()])
    text = open('synonymize/hounds_sherlock.txt').read().replace('_', ' ')

    bot = POSifiedText(text)

    try:
        while True:
            cmd = input('Generate sentence?')

            if cmd.lower() in ['n', 'no', 'q', 'quit']:
                break

            print(pipe(bot.make_sentence()))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
