import os
import random
from os import path
from typing import List, Tuple

import pycorpora
from pincelate import Pincelate
from textgenrnn import textgenrnn

from .abstracts import Namor


class SoundNamor(Namor):
    def __init__(self, corpus: List[str]):
        self.pin = Pincelate()

        corpus = [self.pin.soundout(x.lower()) for x in corpus]
        max_length = max(map(len, corpus))

        file_name = 'models/sound_namor.hdf5'
        if path.isfile(file_name):
            self.rnn = textgenrnn(file_name, name='sound_namor')
        else:
            self.rnn = textgenrnn()
            self.rnn.train_on_texts(
                [' '.join(x) for x in corpus],
                num_epochs=10,
                max_gen_length=max_length,
                new_model=True)
            # TODO: Finetune epoch count

            self.rnn.save(file_name)
            os.remove('textgenrnn_weights.hdf5')

    def generate_name(self, sex: str) -> Tuple[str, str]:
        return self.pin.spell(self.rnn.generate(
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
