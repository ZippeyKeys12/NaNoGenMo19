import csv
import random
from typing import Tuple

from tracery import Grammar

from ..debbi import (FIRST_NAMES_FEMALE, FIRST_NAMES_MALE, LAST_NAMES,
                     NAMES_MEANING)
from .abstracts import Namor


class JesusNamor(Namor):
    def __init__(self):
        dictionary = {
            'F': '#first_name_F#',
            'first_name_F': [],

            'M': '#first_name_M#',
            'first_name_M': [],
        }

        self.last_names = [x for x in LAST_NAMES if x[0] == 'C']

        for name in NAMES_MEANING:
            if name[0] == 'K':
                break

            if name[0] != 'J':
                continue

            if name in FIRST_NAMES_FEMALE:
                dictionary['first_name_F'].append(name)

            elif name in FIRST_NAMES_MALE:
                dictionary['first_name_M'].append(name)

        self.grammar = Grammar(dictionary)

    def generate_name(self, sex: str) -> Tuple[str, str]:
        return (self.grammar.flatten('#{}#'.format(sex)),
                random.choice(self.last_names))


def main():
    namor = JesusNamor()

    try:
        while True:
            cmd = input('Generate name?')

            if cmd.lower() in ['n', 'no', 'q', 'quit']:
                break

            sex = random.choice(['F', 'M'])
            name = namor.generate_name(sex)
            print(sex, ':', ' '.join(name), NAMES_MEANING[name[0]])
    except KeyboardInterrupt:
        pass
