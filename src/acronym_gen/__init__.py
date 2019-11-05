import math
import re
from typing import Dict, List

import requests
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from tracery import Grammar
from tracery.modifiers import base_english

from ..abstracts import Generator


class AcronymGenerator(Generator):
    splitting_pattern = re.compile('[A-Z][^A-Z]*')

    def __init__(self, acronym: str):
        self.acronym = acronym

        dictionary: Dict[str, List[str]] = {}

        splitted = self.splitting_pattern.findall(acronym)

        self.length = len(splitted)

        for start in splitted:
            r = requests.get('https://api.datamuse.com/words', params={
                'sp': '{}*'.format(start)
            })

            dictionary[start] = [obj['word'] for obj in r.json()]

        self.grammar = Grammar(dictionary)
        self.grammar.add_modifiers(base_english)

        self.rule = '#{}.capitalize#'.format('.capitalize# #'.join(splitted))

    def generate_text(self) -> str:
        return '\n'.join((self.grammar.flatten(self.rule)
                          for _ in range(math.ceil(50000 / self.length))))

    def save_to_file(self, name):
        doc = SimpleDocTemplate(name, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Normal_CENTER',
                                  parent=styles['Normal'],
                                  alignment=TA_CENTER))

        doc.build([Paragraph(
            '<font size="18">{}</font>'.format(self.acronym),
            styles['Normal_CENTER']),
            Spacer(1, 12)] +
            [Paragraph(p, styles['Normal_CENTER'])
             for p in self.generate_text().split('\n')])


def main():
    gen = AcronymGenerator('NaNoGenMo')

    gen.save_to_file('acronym_gen.pdf')


if __name__ == "__main__":
    main()
