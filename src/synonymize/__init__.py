import re
from collections import defaultdict
from typing import Dict, List

import markovify
import nltk
import requests
import spacy
from cytoolz.functoolz import pipe
from nltk.corpus import wordnet as wn
from textacy.preprocessing import (normalize_hyphenated_words,
                                   normalize_quotation_marks,
                                   normalize_unicode, normalize_whitespace)
from tracery import Grammar
from tracery.modifiers import base_english

from ..abstracts import Generator
from ..util import UNIVERSAL_TO_LETTER, word_count


class POSifiedText(markovify.Text, Generator):
    separator = "<:>"
    clean_pattern = re.compile(r'[\n_]')
    tracery_pattern = re.compile(r'^#.+#$')

    def __init__(self, input_text: str, state_size: int = 2):
        nltk.download('brown')
        nltk.download('gutenberg')
        self.nlp = spacy.load('en_core_web_lg')

        self.synonyms: Dict[str, List[str]] = defaultdict(list)
        self.entities: Dict[str, List[str]] = defaultdict(list)

        input_text = pipe(
            input_text,
            # lambda x: x.replace('\n', ' '),
            lambda x: self.clean_pattern.sub(' ', x),
            normalize_hyphenated_words,
            normalize_quotation_marks,
            normalize_unicode,
            normalize_whitespace
        )

        markovify.Text.__init__(
            self, input_text, state_size, retain_original=False)

        self.grammar = Grammar({**self.synonyms, **self.entities})
        self.grammar.add_modifiers(base_english)

    def sentence_join(self, sentences):
        return " ".join(sentences)

    def word_split(self, sentence):
        tokenized = []
        first = True
        entity = False

        entity_construct = {"tag": "", "type": "", "words": []}
        for word in self.nlp(sentence):
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

            if word.pos_ in {'NOUN', 'VERB'}:
                # syns = wn.synsets(word.orth_, self.pos_converter[word.pos_])

                modifiers = []

                if word.orth_ not in self.synonyms:
                    r = requests.get('https://api.datamuse.com/words', params={
                        'ml': word.orth_
                    })

                    syns = []
                    if len(r.json()) > 0:
                        syns = [
                            obj['word'] for obj in r.json()
                            if 'syn' in obj['tags'] and
                            UNIVERSAL_TO_LETTER[word.pos_] in obj['tags'] and
                            'prop' not in obj['tags']]

                    if len(syns) > 0:
                        self.synonyms[word.orth_] = syns
                    else:
                        self.synonyms[word.orth_] = False

                if self.synonyms[word.orth_]:
                    default = False

                    if (not (first or entity) and
                            tokenized[-1].lower() in {'a', 'an'}):
                        if tokenized[-1] != tokenized[-1].lower():
                            first = True
                        modifiers.append('.a')

                    if not first and word.orth_[0].isupper():
                        modifiers.append('.capitalize')

                    if entity:
                        text = '#{}{}#'.format(word.orth_, ''.join(modifiers))
                    else:
                        text = self.separator.join(('#{}{}#'.format(
                            word.orth_, ''.join(modifiers)), word.tag_))

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
            (word, _) = word.split(self.separator)
            sentence.append(self.grammar.flatten(word))

        return " ".join(sentence).replace('_', ' ')

    def generate_text(self, **kwargs) -> str:
        length = kwargs.get('length', 50000)

        text = ''
        w_count = 0

        while w_count < length:
            sent = self.make_sentence()
            text += sent
            w_count += word_count(sent)

        return text

    def save_to_file(self, file_name: str, length: int = 50000):
        text = self.generate_text(length=length)

        with open(file_name, 'w') as f:
            f.write(text)


def main():
    # corpus = "\n".join([gt.raw(fileid) for fileid in gt.fileids()])
    # corpus = '\n'.join([' '.join(s) for s in brown.sents()])
    text = open('src/synonymize/hounds_sherlock.txt').read().replace('_', ' ')

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
