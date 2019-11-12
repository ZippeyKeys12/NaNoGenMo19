import datetime
import random
import re
from typing import Any, Dict, List

from faker import Faker
from faker.providers import address, profile
from tracery import Grammar
from tracery.modifiers import base_english
from us import states

from ..abstracts import Generator
from ..shared import CleaningProcessor


class AutBioGenerator(Generator):
    raw_pattern = re.compile(r'^\(\((.+)\)\)$')
    state_pattern = re.compile(r', ([A-Z]{2}) [0-9]{5}$')

    def __init__(self):
        self.cleaner = CleaningProcessor()

        self.fake = Faker()
        self.fake.add_provider(address)
        self.fake.add_provider(profile)

        dictionary: Dict[str, List[str]] = {
            'cred_romance': ['USA Today bestselling',
                             'RITA Award winning', '#cred_gen#'],

            'cred_sci-fi': ['#scifantasy_award# Award winning',
                            '#scifi_award# Award winning', '#cred_gen#'],
            'scifi_award': ['BSFA', 'Philip K. Dick'],

            'cred_fantasy': ['#scifantasy_award# Award winning',
                             '#scifi_award# Award winning', '#cred_gen#'],
            'fantasy_award': ['British Fantasy', 'World Fantasy', 'Gemmell',
                              'Mythopoeic'],

            'scifantasy_award': ['Hugo', 'Nebula', 'Locus', 'Aurealis'],

            'cred_gen': ['#top_award# Prize winning',
                         'New York Times bestselling'],
            'top_award': ['Pulitzer', 'Booker', 'Nobel'],

            'good_adj': ['thrilling', 'fascinating', 'revolutionary',
                         'breathtaking', 'beautiful', 'seminal'],


            'married_and_kids': 'with #Their# #spouse# and #children#',

            'married': 'with #Their# #spouse#',

            'kids': 'with #Their# #children#',
            'children': ['#num_kids# kids', '#num_kids# #kid_type.s#',
                         '#kid_type#'],
            'kid_type': ['daughter', 'son'],
            'num_kids': 4 * ['2'] + ['3']
        }

        def raw(text, **params):
            try:
                return self.raw_pattern.match(text).group(1)
            except AttributeError:
                return text

        self.grammar = Grammar(dictionary)
        self.grammar.add_modifiers(base_english)
        self.grammar.add_modifiers({
            'raw': raw,
            'clean': lambda x: x >> self.cleaner
        })

    def get_astrological_sign(self, birthdate: datetime.date) -> str:
        return {
            1: 'capricorn' if birthdate.day < 20 else 'aquarius',
            2: 'aquarius' if birthdate.day < 19 else 'pisces',
            3: 'pisces' if birthdate.day < 21 else 'aries',
            4: 'aries' if birthdate.day < 20 else 'taurus',
            5: 'taurus'if birthdate.day < 21 else 'gemini',
            6: 'gemini'if birthdate.day < 21 else 'cancer',
            7: 'cancer'if birthdate.day < 23 else 'leo',
            8: 'leo'if birthdate.day < 23 else 'virgo',
            9: 'virgo'if birthdate.day < 23 else 'libra',
            10: 'libra'if birthdate.day < 23 else 'scorpio',
            11: 'scorpio' if (birthdate.day < 22) else 'sagittarius',
            12: 'sagittarius' if (birthdate.day < 22) else 'capricorn'
        }[birthdate.month]

    def get_zodiac_sign(self, birthdate: datetime.date) -> str:
        return {
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
        }[(birthdate.year - 1900) % 12]

    def generate_details(self, **kwargs) -> dict:
        details: Dict[str, Any] = {
            'genre': random.choice(['sci-fi', 'fantasy'])
        }

        details.update(self.fake.profile(sex=None))

        details['pronouns'] = {
            'F': '[They:she][Them:her][Their:her][Theirs:hers]',
            'M': '[They:he][Them:him][Their:his][Theirs:his]'
        }.get(details['sex'],
              '[They:they][Them:them][Their:their][Theirs:theirs]')

        details['is_gay'] = random.random() < .023
        details['is_married'] = random.random() < .43
        details['has_kids'] = random.random() < .74

        if details['is_married']:
            if details['is_gay']:
                details['spouse'] = {
                    'F': 'wife',
                    'M': 'husband'
                }[details['sex']]
            else:
                details['spouse'] = {
                    'F': 'husband',
                    'M': 'wife'
                }[details['sex']]

        addr = self.state_pattern.search(details['residence'])
        while not addr:
            details['residence'] = self.fake.address()

            addr = self.state_pattern.search(details['residence'])

        details['state'] = states.lookup(addr.group(1)).name

        details['signs'] = {
            'astrological': self.get_astrological_sign(details['birthdate']),
            'zodiac': self.get_zodiac_sign(details['birthdate'])
        }

        if random.random() < .3:
            details['inspired_by'] = {
                'sex': random.choice(['F', 'M'])
            }

            details['inspired_by']['relation'] = random.choice({
                'F': ['mother', 'sister', 'daughter'],
                'M': ['father', 'brother', 'son']
            }[details['inspired_by']['sex']])
        else:
            details['inspired_by'] = None

        return details

    def generate_text(self, **kwargs) -> str:
        details = kwargs.get('details', self.generate_details())

        text = """
            {name} is a #cred_{genre}# author of #good_adj# {genre} #books.raw#
            who lives in {state}
        """

        if details['is_married']:
            if details['has_kids']:
                text += ' #{pronouns}[spouse:{spouse}]married_and_kids#'
            else:
                text += ' #{pronouns}[spouse:{spouse}]married#'

        elif details['has_kids']:
            text += ' #{pronouns}kids#'

        text += '.'

        print(text)
        return self.grammar.flatten(text.format(**details)) >> self.cleaner


def main():
    gen = AutBioGenerator()

    for _ in range(5):
        dets = gen.generate_details()
        print(dets)

        print(gen.generate_text(details=dets))


if __name__ == "__main__":
    main()
