import os
import random
from os import path
from typing import Dict, List, Tuple

import pycorpora
from pincelate import Pincelate
from textgenrnn import textgenrnn

from .abstracts import Namor


class SoundNamor(Namor):
    def __init__(self, corpus: Dict[str, List[str]]):
        self.pin = Pincelate()

        corpus = {k: [self.pin.soundout(v.lower())
                      for x in v] for k, v in corpus}
        max_length = max(map(len, corpus))

        self.rnn: Dict[str, textgenrnn] = {}
        file_name = 'models/sound_namor_{}.hdf5'.format
        for sex in {'F', 'M'}:
            if path.isfile(file_name(sex)):
                self.rnn[sex] = textgenrnn(file_name, name=file_name(sex))

            else:
                self.rnn[sex] = textgenrnn(name='sound_namor_{}'.format(sex))

                self.rnn[sex].train_on_texts(
                    [' '.join(x) for x in corpus[sex]],
                    num_epochs=10,
                    max_gen_length=max_length,
                    new_model=True)
                # TODO: Finetune epoch count

                self.rnn[sex].save(file_name)

    def generate_name(self, sex: str) -> Tuple[str, str]:
        return self.pin.spell(self.rnn[sex].generate(
            return_as_list=True)[0].split(' ')).capitalize()


def main():
    # TODO: Replace with better, sex-separated data
    namor = SoundNamor(
        pycorpora.get_file('humans', 'firstNames')['firstNames'])

    try:
        while True:
            cmd = input('Generate name?')

            if cmd.lower() in ['n', 'no', 'q', 'quit']:
                break

            sex = random.choice(['F', 'M'])
            print(sex, ':', ''.join(namor.generate_name(sex)))
    except KeyboardInterrupt:
        pass
