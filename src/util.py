import re

from nltk.corpus import wordnet as wn

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


def word_count(text: str):
    return len(WHITESPACE_PATTERN.split(text))
