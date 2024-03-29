import csv
import datetime
import re
from collections import defaultdict
from functools import lru_cache
from typing import DefaultDict, Dict, List, Optional

import nltk
import pycorpora
from faker.providers.person.en import Provider
from nltk.corpus import names

from ..util import word_similarity


def get_pronouns(sex: Optional[str]) -> str:
    return {
        'F': '[They:she][Them:her][Their:her][Theirs:hers]',
        'M': '[They:he][Them:him][Their:his][Theirs:his]'
    }.get(details['sex'],
          '[They:they][Them:them][Their:their][Theirs:theirs]')


@lru_cache()
def ASTROLOGICAL(day):
    return {
        1: 'capricorn' if day < 20 else 'aquarius',
        2: 'aquarius' if day < 19 else 'pisces',
        3: 'pisces' if day < 21 else 'aries',
        4: 'aries' if day < 20 else 'taurus',
        5: 'taurus'if day < 21 else 'gemini',
        6: 'gemini'if day < 21 else 'cancer',
        7: 'cancer'if day < 23 else 'leo',
        8: 'leo'if day < 23 else 'virgo',
        9: 'virgo'if day < 23 else 'libra',
        10: 'libra'if day < 23 else 'scorpio',
        11: 'scorpio' if day < 22 else 'sagittarius',
        12: 'sagittarius' if day < 22 else 'capricorn'
    }


def get_astrological_sign(birthdate: datetime.date) -> str:
    return ASTROLOGICAL(birthdate.day)[birthdate.month]


ZODIAC = {
    0: 'rat',
    1: 'ox',
    2: 'tiger',
    3: 'rabbit',
    4: 'dragon',
    5: 'snake',
    6: 'horse',
    7: 'goat',
    8: 'monkey',
    9: 'rooster',
    10: 'dog',
    11: 'pig'
}


def get_zodiac_sign(birthdate: datetime.date) -> str:
    return ZODIAC[(birthdate.year - 1900) % 12]


@lru_cache()
def get_astrological_traits(astrological_sign: str) -> List[str]:
    return pycorpora.get_file('divination', 'zodiac')[
        'western_zodiac'][astrological_sign.capitalize()]['keywords']


ASTRO_TAROT: DefaultDict[str, List[str]] = defaultdict(list)


@lru_cache()
def get_tarot_cards(astrological_sign: str) -> List[str]:
    if len(ASTRO_TAROT) == 0:
        tarots = pycorpora.get_file('divination', 'tarot_interpretations')[
            'tarot_interpretations']
        for tarot in tarots:
            signs: Dict[str, float] = {}
            for sign, traits in zip(ZODIAC.values(), map(
                    get_astrological_traits, ZODIAC.values())):
                keywords = get_tarot_keywords(tarot['name'])

                avg: float = 0
                for keyword in keywords:
                    avg += sum(map(
                        lambda x: word_similarity(keyword, x), traits))
                avg /= len(keywords)

                signs[sign] = avg

            ASTRO_TAROT[min(signs.items(), key=lambda x: x[1])[0]] = tarot

    return ASTRO_TAROT[astrological_sign]


tarot_keywords = {x['name']: x['keywords'] for x in pycorpora.get_file(
    'divination', 'tarot_interpretations')['tarot_interpretations']}


@lru_cache()
def get_tarot_keywords(tarot_card: str) -> List[str]:
    return tarot_keywords[tarot_card]


nltk.download('names')

FIRST_NAMES_FEMALE = frozenset(
    names.words('female.txt') +
    list(Provider.first_names_female))

FIRST_NAMES_MALE = frozenset(
    names.words('male.txt') +
    list(Provider.first_names_male))

LAST_NAMES = frozenset(Provider.last_names)


def name_meanings():
    ret: Dict[str, List[str]] = {}

    with open('data/names.csv') as csvfile:
        name_pattern = re.compile(
            r'(Pet form|From|Form|See|Dim\.) (of )?(the name )?([A-Z]+)( (or|&) ([A-Z]+))?')
        names_reader = csv.reader(csvfile)

        for row in names_reader:
            name = row[0].lower().capitalize()

            ret[name] = [row[1]]

            if len(row) > 2 and row[2] != '':
                ret[name].append(row[2])

        for name in ret:
            for i, meaning in enumerate(ret[name]):
                match = name_pattern.match(meaning)

                if match:
                    try:
                        new = ret[match.group(4).lower().capitalize()]
                    except KeyError:
                        continue

                    ret[name][i] = new[0]

                    if len(new) > 1:
                        ret[name].extend(new[1:])

                    if match.group(7):
                        try:
                            new = ret[match.group(7).lower().capitalize()]
                        except KeyError:
                            continue

                        ret[name][i] = new[0]

                        if len(new) > 1:
                            ret[name].extend(new[1:])

    return ret


NAMES_MEANING: Dict[str, List[str]] = name_meanings()
