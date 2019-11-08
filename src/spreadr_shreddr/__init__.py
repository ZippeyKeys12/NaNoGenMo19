import re
import textwrap
from collections import OrderedDict
from itertools import combinations
from os import path
from typing import Dict, List, Optional, Set, Tuple, cast

import nltk
import pycorpora
import requests
import spacy
import yaml
from cytoolz.functoolz import pipe
from nltk import sent_tokenize
from nltk.corpus import wordnet as wn
from spacy.tokens import Token
from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer
from textacy.preprocessing import (normalize_hyphenated_words,
                                   normalize_quotation_marks,
                                   normalize_unicode, normalize_whitespace)

from ..abstracts import Generator
from ..util import (UNIVERSAL_TO_DATAMUSE, WHITESPACE_PATTERN, get_stop_words,
                    list_sums, word_count)


class SpreadShredGenerator(Generator):
    separator = "<:>"
    clean_pattern = re.compile('[\n_]')

    def __init__(self, input_text: str):
        nltk.download('punkt')

        self.nlp = spacy.load('en_core_web_lg')

        self.summarizer = LsaSummarizer(Stemmer('english'))
        self.summarizer.stop_words = get_stop_words('english')

        self.synonyms: Dict[str, Optional[List[str]]] = {}
        if path.isfile('src/spreadr_shreddr/syns.yaml'):
            with open('src/spreadr_shreddr/syns.yaml', 'r') as f:
                self.synonyms = yaml.safe_load(f)

        if self.synonyms is None:
            self.synonyms = {}

        self.patterns: Dict[str, str] = OrderedDict()
        self.rev_patterns: Dict[str, str] = OrderedDict()

        with open('src/spreadr_shreddr/data.yaml', 'r') as f:
            data = yaml.safe_load(f)

        self.patterns.update(data['shorten'])
        self.patterns.update(data['expand'])

        data['filler'].extend(pycorpora.get_file(
            'humans', 'prefixes')['prefixes'])

        self.patterns.update({k: '' for k in data['filler']})

        for obj in pycorpora.get_file('words', 'compounds')['compounds']:
            key = '{} {}'.format(obj['firstWord'], obj['secondWord'])
            if key not in self.patterns:
                self.patterns[key] = obj['compoundWord']

        self.patterns.update({
            k.capitalize(): v.capitalize()
            for k, v in self.patterns.items()
        })

        self.brits = data['brit_am']
        self.murcans = {v: k for k, v in self.brits.items()}

        def clean(text: str):
            return pipe(
                text,
                lambda x: self.clean_pattern.sub(' ', x),
                normalize_hyphenated_words,
                normalize_quotation_marks,
                normalize_unicode,
                normalize_whitespace
            )

        self.cleaned_text: str = clean(input_text)

        with open('spreadr_shreddr_base.txt', 'w') as f:
            f.write(self.cleaned_text)

        self.paragraphs = {clean(p): word_count(clean(p))
                           for p in input_text.split('\n\n')}

        changed = False
        for sent in sent_tokenize(self.cleaned_text):
            for index, word in enumerate(self.nlp(sent)):
                orth = word.orth_.lower()
                key = self.separator.join((orth, word.tag_))

                if key not in self.synonyms:
                    changed = True
                    syns: List[str] = []

                    if (word.pos_ in UNIVERSAL_TO_DATAMUSE and
                            len(wn.synsets(orth)) <= 1):
                        r = requests.get('https://api.datamuse.com/words',
                                         params={'ml': orth})

                        if len(r.text) > 0:
                            syns = self.get_synonyms(
                                ' '.join(sent), (index, word), r.json())

                    if len(syns) > 0:
                        self.synonyms[key] = syns
                    else:
                        self.synonyms[key] = None

                if changed:
                    changed = False
                    with open('src/spreadr_shreddr/syns.yaml', 'a') as f:
                        f.write(yaml.dump({key: self.synonyms[key]}))

    def get_synonyms(self, sentence: str, word: Tuple[int, Token],
                     candidates: list) -> List[str]:
        def tagged(x):
            return ('tags' in x and 'syn' in x['tags'] and
                    'prop' not in x['tags'] and word_count(x['word']) == 1)

        def match_pos(x):
            return (word[1].tag_ == self.nlp(
                sentence.replace(word[1].orth_, x['word']))[word[0]].tag_ and
                UNIVERSAL_TO_DATAMUSE[word[1].pos_] in x['tags'])

        return [word[1].orth_] + [obj['word'] for obj in candidates
                                  if tagged(obj) and match_pos(obj)]

    def replace_synonym(
            self, word: Token, desired_char_change: int) -> Tuple[str, int]:
        key = self.separator.join((word.orth_.lower(), word.tag_))

        if key in self.synonyms and self.synonyms[key] is not None:
            length = len(word.orth_)
            ideal = min(cast(List[str], self.synonyms[key]),
                        key=lambda x: abs(
                            desired_char_change + length - len(x)))

            return (ideal, desired_char_change + length - len(ideal))

        return (word.orth_, desired_char_change)

    def brit_am(
            self, word: Token, desired_char_change: int) -> Tuple[str, int]:
        length = len(word.orth_)
        ideal = word.orth_

        if desired_char_change < 0 and word.orth_ in self.brits:
            ideal = self.brits[word.orth_]

        if desired_char_change > 0 and word.orth_ in self.murcans:
            ideal = self.murcans[word.orth_]

        return (ideal, desired_char_change + length - len(ideal))

    def summarize(self, excerpt: str, len_s: int) -> str:
        parser = PlaintextParser.from_string(excerpt, Tokenizer('english'))

        document = parser.document
        dictionary = self.summarizer._create_dictionary(document)

        if dictionary is None:
            return excerpt

        words_count = len(dictionary)
        sentences_count = len(document.sentences)
        if words_count < sentences_count:
            return excerpt

        sents = self.summarizer(parser.document, len_s)

        return ' '.join(str(s) for s in sents)

    def generate_text(self, word_length: int = None,
                      char_length: int = None) -> str:
        text = self.cleaned_text

        # Setup
        dchar_change = 0
        if char_length is not None:
            dchar_change = char_length - len(text)

        dword_change = 0
        if word_length is not None:
            dword_change = word_length - word_count(text)
            print('a', dword_change)

        # Summarize paragraphs
        if dword_change < 0:
            paragraphs = sorted(
                self.paragraphs, key=lambda x: len(PlaintextParser.from_string(
                    x, Tokenizer('english')).document.sentences), reverse=True)

            ideals: List[Tuple[int, str, str]] = []
            d = {}
            for len_s in range(1, len(PlaintextParser.from_string(
                    paragraphs[0], Tokenizer('english')).document.sentences)):
                for p in paragraphs:
                    if len(PlaintextParser.from_string(
                            p, Tokenizer('english')).document.sentences) <= len_s:
                        break

                    repl = self.summarize(p, len_s)
                    diff = word_count(repl) - self.paragraphs[p]

                    if diff == 0:
                        continue

                    d[repl] = p

                    ideals.append((diff, p, repl))

            # with open('aaa.yaml', 'w') as f:
            #     yaml.dump(d, f)

            # Check paragraph combinations
            possible = list_sums((x[0] for x in ideals), dword_change)
            if len(possible) > 0:
                for diff, p, repl in min(possible, key=len):
                    text = text.replace(p, '{}\n\n'.format(repl))

                    dword_change -= diff

                    if char_length is not None:
                        dchar_change -= len(repl) - len(p)
            else:
                excluded: Set[str] = set()
                for diff, p, repl in sorted(
                        ideals, key=lambda x: abs(dword_change - x[0]), reverse=True):
                    if (abs(dword_change - diff) < abs(dword_change) and
                            p not in excluded):
                        excluded.add(p)

                        text = text.replace(p, '{}\n\n'.format(repl))

                        dword_change -= diff

                        if char_length is not None:
                            dchar_change -= len(repl) - len(p)

        def space(x):
            return WHITESPACE_PATTERN.sub(' ', ' {} '.format(x))

        # Patterns for word count
        done: Set[str] = set()
        while dword_change < 0 and len(done) != len(self.patterns):
            done.clear()
            for k, v in self.patterns.items():
                if dword_change == 0 and dchar_change == 0:
                    print('b', dword_change)
                    return text

                if v == '':
                    diff = -word_count(k)
                else:
                    diff = word_count(v) - word_count(k)

                if(abs(dword_change - diff) < abs(dword_change) and
                        text.find(space(k)) != -1):
                    text = text.replace(space(k), space(v), 1)

                    dword_change -= diff
                    if char_length is not None:
                        dchar_change -= len(v) - len(k)

                else:
                    done.add(k)

        # Synonyms and spellings for char count
        for word in self.nlp(text):
            if dword_change == 0 and dchar_change == 0:
                print('c', dword_change)
                return text

            while dchar_change != 0 and text.find(space(word.orth_)) != -1:
                (repl, dchar_change) = self.replace_synonym(
                    word, dchar_change)
                text = text.replace(space(word.orth_), space(repl), 1)

            while dchar_change != 0 and text.find(space(word.orth_)) != -1:
                (repl, dchar_change) = self.brit_am(word, dchar_change)
                text = text.replace(space(word.orth_), space(repl), 1)

        print('d', dword_change)
        return text

    def save_to_file(self, file_name: str, length: int = 50000):
        text = self.generate_text(length)

        with open(file_name, 'w') as f:
            f.write('\n'.join(textwrap.wrap(text)))


def main():
    text = open('src/synonymize/hounds_sherlock.txt').read().replace('_', '')

    gen = SpreadShredGenerator(text)

    gen.save_to_file('spreadr_shreddr.txt')


if __name__ == "__main__":
    main()
