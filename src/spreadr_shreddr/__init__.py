import re
from collections import OrderedDict
from os import path
from typing import Dict, List, Optional, Tuple, cast

import markovify
import requests
import spacy
import yaml
from cytoolz.functoolz import pipe
from nltk.corpus import wordnet as wn
from spacy.tokens import Token
from textacy.preprocessing import (normalize_hyphenated_words,
                                   normalize_quotation_marks,
                                   normalize_unicode, normalize_whitespace)

from ..abstracts import Generator
from ..util import UNIVERSAL_TO_DATAMUSE, word_count


class SqueezerGenerator(Generator):
    separator = "<:>"
    clean_pattern = re.compile('[\n_]')

    def __init__(self, input_text: str):
        self.nlp = spacy.load('en_core_web_lg')

        self.synonyms: Dict[str, Optional[List[str]]] = {}
        if path.isfile('src/squeezr/syns.yaml'):
            with open('src/squeezr/syns.yaml', 'r') as f:
                self.synonyms = yaml.safe_load(f)

        if self.synonyms is None:
            self.synonyms = {}

        self.patterns: Dict[str, str] = OrderedDict()

        with open('src/squeezr/data.yaml', 'r') as f:
            data = yaml.safe_load(f)

        self.patterns.update(data['contractions'])
        self.patterns.update(data['acronyms'])

        self.rev_patterns = {v: k for k, v in self.patterns.items()}

        self.brits = data['brit_am']
        self.murcans = {v: k for k, v in self.brits.items()}

        self.filler_words = data['filler']

        self.input_text: str = pipe(
            input_text,
            # lambda x: x.replace('\n', ' ')
            lambda x: self.clean_pattern.sub(' ', x),
            normalize_hyphenated_words,
            normalize_quotation_marks,
            normalize_unicode,
            normalize_whitespace
        )

        changed = False
        for word in self.nlp(self.input_text):
            orth = word.orth_.lower()
            key = self.separator.join((orth, word.tag_))

            if key not in self.synonyms:
                changed = True
                syns: List[str] = []

                if (word.pos_ in UNIVERSAL_TO_DATAMUSE and
                        len(wn.synsets(orth)) <= 1):
                    r = requests.get('https://api.datamuse.com/words', params={
                        'ml': orth
                    })

                    if len(r.text) > 0:
                        syns = [orth]+[
                            obj['word'] for obj in r.json()
                            if 'tags' in obj and
                            'syn' in obj['tags'] and
                            word.tag_ == self.nlp(obj['word'])[0].tag_ and
                            UNIVERSAL_TO_DATAMUSE[word.pos_] in obj['tags'] and
                            'prop' not in obj['tags']]

                if len(syns) > 0:
                    self.synonyms[key] = syns
                else:
                    self.synonyms[key] = None

            if changed:
                changed = False
                with open('src/squeezr/syns.yaml', 'a') as f:
                    f.write(yaml.dump({key: self.synonyms[key]}))

    def replace_synonym(self, word: Token, desired_change: int) -> str:
        key = self.separator.join((word.orth_.lower(), word.tag_))

        if self.synonyms[key] is not None:
            length = len(word.orth_)

            return min(cast(List[str], self.synonyms[key]),
                       key=lambda x: abs(desired_change-len(
                           x.split(self.separator)[0])+length))

        return word.orth_

    def brit_am(self, word: Token, desired_char_change: int) -> str:
        if desired_char_change < 0 and word.orth_ in self.brits:
            return self.brits[word.orth_]

        if desired_char_change > 0 and word.orth_ in self.murcans:
            return self.murcans[word.orth_]

        return word.orth_

    @staticmethod
    def get_desired_change(
        text: str, word_length: int = 0, char_length: int = 0
    ) -> Tuple[int, int]:
        desired_char_change = 0
        if char_length != 0:
            desired_char_change = char_length - len(text)

        desired_word_change = 0
        if word_length != 0:
            desired_word_change = word_length - word_count(text)

        return (desired_word_change, desired_char_change)

    def generate_text(self, word_length: int = 0,
                      char_length: int = 0) -> str:
        text = self.input_text

        dword_change, dchar_change = self.get_desired_change(
            text, word_length, char_length)

        for word in self.filler_words:
            if dword_change == 0 and dchar_change == 0:
                return text

            while dword_change < 0 and text.find(word) != -1:
                text = text.replace(' {} '.format(word), ' ')

                dword_change, dchar_change = self.get_desired_change(
                    text, word_length, char_length)

        for k, v in self.patterns.items():
            if dword_change == 0 and dchar_change == 0:
                return text

            while dword_change < 0 and text.find(k) != -1:
                text = text.replace(k, v, 1)

                dword_change, dchar_change = self.get_desired_change(
                    text, word_length, char_length)

            while dword_change > 0 and text.find(k) != -1:
                text = text.replace(v, k, 1)

                dword_change, dchar_change = self.get_desired_change(
                    text, word_length, char_length)

        for word in self.nlp(text):
            if dword_change == 0 and dchar_change == 0:
                return text

            if dchar_change != 0:
                text = text.replace(
                    word.orth_, self.replace_synonym(word, dchar_change), 1)

                dword_change, dchar_change = self.get_desired_change(
                    text, word_length, char_length)

            if dchar_change != 0:
                text = text.replace(
                    word.orth_, self.brit_am(word, dchar_change), 1)

                dword_change, dchar_change = self.get_desired_change(
                    text, word_length, char_length)

        return text

    def save_to_file(self, file_name: str, length: int = 50000):
        text = self.generate_text(length)

        with open(file_name, 'w') as f:
            f.write(text)


def main():
    text = open('src/synonymize/hounds_sherlock.txt').read().replace('_', ' ')

    gen = SqueezerGenerator(text)

    gen.save_to_file('squeezr.txt')


if __name__ == "__main__":
    main()
