import datetime
import re
from typing import FrozenSet, cast

from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from spacy.lang.en.stop_words import STOP_WORDS
from sumy.utils import get_stop_words as getsw

import spacy

PENN_TO_UNIVERSAL = {
    '#': 'SYM',
    '$': 'SYM',
    '"': 'PUNCT',
    ',': 'PUNCT',
    '-LRB-': 'PUNCT',
    '-RRB-': 'PUNCT',
    '.': 'PUNCT',
    ':': 'PUNCT',
    'AFX': 'ADJ',
    'CC': 'CCONJ',
    'CD': 'NUM',
    'DT': 'DET',
    'EX': 'PRON',
    'FW': 'X',
    'HYPH': 'PUNCT',
    'IN': 'ADP',
    'JJ': 'ADJ',
    'JJR': 'ADJ',
    'JJS': 'ADJ',
    'LS': 'X',
    'MD': 'VERB',
    'NIL': 'X',
    'NN': 'NOUN',
    'NNP': 'PROPN',
    'NNS': 'PROPN',
    'PDT': 'DET',
    'POS': 'PART',
    'PRP': 'PRON',
    'PRP$': 'DET',
    'RB': 'ADV',
    'RBR': 'ADV',
    'RBS': 'ADV',
    'RP': 'ADP',
    'SYM': 'SYM',
    'TO': 'PART',
    'UH': 'INTJ',
    'VB': 'VERB',
    'VBD': 'VERB',
    'VBG': 'VERB',
    'VBN': 'VERB',
    'VBP': 'VERB',
    'VBZ': 'VERB',
    'WDT': 'DET',
    'WP': 'PRON',
    'WP$': 'DET',
    'WRB': 'ADV',
    '``': 'PUNCT'
}

UNIVERSAL_TO_LETTER = {
    "ADJ": wn.ADJ,
    "ADV": wn.ADV,
    "NOUN": wn.NOUN,
    "VERB": wn.VERB
}

UNIVERSAL_TO_DATAMUSE = {
    "ADJ": 'adj',
    "ADV": 'adv',
    "NOUN": 'n',
    "VERB": 'v'
}

WHITESPACE_PATTERN = re.compile(r'\s+')

WORD2VEC = spacy.load('en_vectors_web_lg')


def word_count(text: str) -> int:
    return len(WHITESPACE_PATTERN.split(text))


def get_stop_words(lang: str) -> FrozenSet[str]:
    tmp = list(stopwords.words(lang))
    tmp.extend(getsw(lang))

    if lang == 'english':
        tmp.extend(STOP_WORDS)

    return cast(FrozenSet[str], frozenset(tmp))


# https://stackoverflow.com/questions/20193555/finding-combinations-to-the-provided-sum-value
def list_sums(lst, target, with_replacement=False):
    def _a(idx, l, r, t, w):
        if t == sum(x[1] for x in l):
            r.append(l)
        elif t < sum(x[1] for x in l):
            return []
        for u in range(idx, len(lst)):
            _a(u if w else (u + 1), l + [(u, lst[u])], r, t, w)
        return r
    return _a(0, [], [], target, with_replacement)


def word_similarity(word1: str, word2: str) -> float:
    return WORD2VEC(word1).similarity(word2)
