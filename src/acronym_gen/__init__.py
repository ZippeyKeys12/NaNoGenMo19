import math
import re
from typing import Dict, List

from datamuse import Datamuse
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from tracery import Grammar
from tracery.modifiers import base_english

from ..abstracts import Generator, Processor


class AcronymGenerator(Generator):
    splitting_pattern = re.compile('[A-Z][^A-Z]*')

    def __init__(self, acronym: str):
        self.acronym = acronym

        api = Datamuse()

        dictionary: Dict[str, List[str]] = {}

        splitted = self.splitting_pattern.findall(acronym)

        self.length = len(splitted)

        for start in splitted:
            res = api.words(sp='{}*'.format(start))

            dictionary[start] = [obj['word'] for obj in res]

        self.grammar = Grammar(dictionary)
        self.grammar.add_modifiers(base_english)

        self.rule = '#{}.capitalize#'.format('.capitalize# #'.join(splitted))

    def generate_text(self, **kwargs) -> str:
        try:
            length = kwargs['length']
        except KeyError:
            length = None
        length = length or 50000

        return '\n'.join((self.grammar.flatten(self.rule)
                          for _ in range(math.ceil(length / self.length))))

    def save_to_file(self, file_name: str, **kwargs):
        try:
            length = kwargs['length']
        except KeyError:
            length = None
        length = length or 50000

        text = self.generate_text(length=length)

        if file_name.endswith('.pdf'):
            doc = SimpleDocTemplate(file_name, pagesize=letter,
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
                 for p in text.split('\n')])
        else:
            with open(file_name, 'w') as f:
                f.write(text)


class AcronymProcessor(Processor):
    splitting_pattern = re.compile('[A-Z][^A-Z]*')

    def __init__(self):
        self.api = Datamuse()

        self.grammar = Grammar({})
        self.grammar.add_modifiers(base_english)

    def process_text(self, input_text: str, **kwargs) -> str:
        splitted = self.splitting_pattern.findall(input_text)

        dictionary: Dict[str, List[str]] = {}
        for start in (x for x in splitted if x not in self.grammar.symbols):
            res = self.api.words(sp='{}*'.format(start), max=1000)

            dictionary[start] = [obj['word'] for obj in res]

        for k, v in dictionary.items():
            self.grammar.push_rules(k, v)

        return self.grammar.flatten('#{}.capitalize#'.format(
            '.capitalize# #'.join(splitted)))


def main():
    gen = AcronymGenerator('NaNoGenMo')

    gen.save_to_file('acronym_gen.pdf')


if __name__ == "__main__":
    main()
