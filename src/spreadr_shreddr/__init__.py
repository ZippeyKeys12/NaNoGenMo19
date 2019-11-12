from collections import OrderedDict
from os import path
from typing import Dict, List, Optional, Set, Tuple, cast

import nltk
import pycorpora
import spacy
import yaml
from cytoolz.functoolz import pipe
from datamuse import Datamuse
from nltk import sent_tokenize
from nltk.corpus import wordnet as wn
from spacy.tokens import Token
from sumy.nlp.stemmers import Stemmer
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer

from ..abstracts import Processor
from ..shared import CleaningProcessor, TextWrapProcessor
from ..util import (UNIVERSAL_TO_DATAMUSE, WHITESPACE_PATTERN, get_stop_words,
                    list_sums, word_count)


class SpreadShredProcessor(Processor):
    separator = "<:>"

    def __init__(self, input_texts: str):
        nltk.download('punkt')

        self.nlp = spacy.load('en_core_web_lg')

        self.summarizer = LsaSummarizer(Stemmer('english'))
        self.summarizer.stop_words = get_stop_words('english')

        self.cleaner = CleaningProcessor()

        self.synonyms: Dict[str, Optional[List[str]]] = {}
        if path.isfile('src/syns.yaml'):
            with open('src/syns.yaml', 'r') as f:
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

        changed = False
        api = Datamuse()
        for text in input_texts:
            text >>= self.cleaner

            for sent in sent_tokenize(text):
                for index, word in enumerate(self.nlp(sent)):
                    orth = word.orth_.lower()
                    key = self.separator.join((orth, word.tag_))

                    if key not in self.synonyms:
                        changed = True
                        syns: List[str] = []

                        if (word.pos_ in UNIVERSAL_TO_DATAMUSE and
                                len(wn.synsets(orth)) <= 1):
                            res = api.words(ml=orth)

                            if len(res) > 0:
                                syns = self._get_synonyms(
                                    ' '.join(sent), (index, word), res)

                        if len(syns) > 1:
                            self.synonyms[key] = syns
                        else:
                            self.synonyms[key] = None

                    if changed:
                        changed = False
                        with open('src/syns.yaml', 'a') as f:
                            f.write(yaml.dump({key: self.synonyms[key]}))

    def _get_synonyms(self, sentence: str, word: Tuple[int, Token],
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

    def process_text(self, input_text: str, **kwargs) -> str:
        cleaned_text = input_text >> self.cleaner

        # Setup
        try:
            char_length = kwargs['char_length']
        except KeyError:
            char_length = None

        dchar_change = 0
        if char_length is not None:
            dchar_change = char_length - len(cleaned_text)

        try:
            word_length = kwargs['word_length']
        except KeyError:
            word_length = None

        dword_change = 0
        if word_length is not None:
            dword_change = word_length - word_count(cleaned_text)
            print('a', dword_change)

        # Summarize paragraphs
        if dword_change < 0:
            paragraphs = {x: word_count(x) for x in (
                p >> self.cleaner for p in input_text.split('\n\n'))}
            pgraph_keys = sorted(
                paragraphs, key=lambda x: len(PlaintextParser.from_string(
                    x, Tokenizer('english')).document.sentences), reverse=True)

            ideals: List[Tuple[int, str, str]] = []
            d = {}
            for len_s in range(1, len(PlaintextParser.from_string(
                    pgraph_keys[0], Tokenizer('english')).document.sentences)):
                for p in pgraph_keys:
                    if len(PlaintextParser.from_string(
                            p, Tokenizer('english')
                    ).document.sentences) <= len_s:
                        break

                    repl = self.summarize(p, len_s)

                    if repl.count('"') % 2 != 0:
                        continue

                    diff = word_count(repl) - paragraphs[p]

                    if diff == 0:
                        continue

                    d[repl] = p

                    ideals.append((diff, p, repl))

            # Check paragraph combinations
            possible = list_sums((x[0] for x in ideals), dword_change)
            if len(possible) > 0:
                for diff, p, repl in min(possible, key=len):
                    cleaned_text = cleaned_text.replace(p, '{}'.format(repl))

                    dword_change -= diff

                    if char_length is not None:
                        dchar_change -= len(repl) - len(p)
            else:
                excluded: Set[str] = set()
                for diff, p, repl in sorted(
                        ideals, key=lambda x: abs(
                            dword_change - x[0]), reverse=True):
                    if (abs(dword_change - diff) < abs(dword_change) and
                            p not in excluded):
                        excluded.add(p)

                        cleaned_text = cleaned_text.replace(
                            p, '{}'.format(repl))

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
                    return cleaned_text

                if v == '':
                    diff = -word_count(k)
                else:
                    diff = word_count(v) - word_count(k)

                if(abs(dword_change - diff) < abs(dword_change) and
                        cleaned_text.find(space(k)) != -1):
                    cleaned_text = cleaned_text.replace(space(k), space(v), 1)

                    dword_change -= diff
                    if char_length is not None:
                        dchar_change -= len(v) - len(k)

                else:
                    done.add(k)

        # Synonyms and spellings for char count
        for word in self.nlp(cleaned_text):
            if dword_change == 0 and dchar_change == 0:
                print('c', dword_change)
                return cleaned_text

            while dchar_change != 0 and cleaned_text.find(space(word.orth_)) != -1:
                (repl, dchar_change) = self.replace_synonym(
                    word, dchar_change)
                cleaned_text = cleaned_text.replace(
                    space(word.orth_), space(repl), 1)

            while dchar_change != 0 and cleaned_text.find(space(word.orth_)) != -1:
                (repl, dchar_change) = self.brit_am(word, dchar_change)
                cleaned_text = cleaned_text.replace(
                    space(word.orth_), space(repl), 1)

        print('d', dword_change)
        return cleaned_text


def main():
    text = open('src/synonymize/hounds_sherlock.txt').read().replace('_', '')

    text = SpreadShredProcessor([text]).process_text(
        text, word_length=50000) >> TextWrapProcessor()

    with open('spreadr_shreddr.txt', 'w') as f:
        f.write(text)


if __name__ == "__main__":
    main()
