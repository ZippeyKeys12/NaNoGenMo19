import string
from typing import List, Optional

import spacy
from cytoolz.functoolz import pipe
from pincelate import Pincelate

from ..abstracts import Processor
from ..shared import CleaningProcessor, TextWrapProcessor


class SoundorProcessor(Processor):
    def __init__(self, temperature: Optional[float] = None):
        self.nlp = spacy.load('en_core_web_lg')
        self.pin = Pincelate()
        self.temperature = temperature
        self.cleaner = CleaningProcessor()

    def process_text(self, input_text: str, **kwargs) -> str:
        temperature = kwargs.get('temperature', self.temperature or .25)

        result: List[str] = []

        for token in self.nlp(input_text >> self.cleaner):
            if any(x not in string.ascii_lowercase for x in token.orth_):
                result.append(token.orth_)

            else:
                new_token = pipe(
                    token.orth_.lower(),
                    lambda x: self.pin.manipulate(x, temperature=temperature)
                )

                if token.orth_ == token.orth_.capitalize():
                    new_token = new_token.capitalize()

                result.append(new_token)

        return ' '.join(result)


def main():
    text = open('src/synonymize/hounds_sherlock.txt').read().replace('_', '')

    text = (text >> CleaningProcessor()
            >> SoundorProcessor()
            >> TextWrapProcessor())

    with open('soundor.txt', 'w') as f:
        f.write(text)


if __name__ == "__main__":
    main()
