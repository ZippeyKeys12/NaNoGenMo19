import datetime
import random

from ..debbi import (get_astrological_sign, get_astrological_traits, get_tarot_cards,
                     get_zodiac_sign)
from ..namor import Namor


class Charrio:
    def __init__(self, namer: Namor):
        self.namer = namer

    def generate_character(self, max_age: int):
        birthdate = datetime.date(datetime.datetime.now().year -
                                  random.choice(range(max_age)))
        ret: dict = {'sex': random.choice(['F', 'M'])}

        astrological = get_astrological_sign(birthdate)

        ret.update({
            'name': self.namer.generate_name(ret['sex']),
            'zodiac': get_zodiac_sign(birthdate),
            'astrological': astrological,
            'tarot': random.choice(get_tarot_cards(astrological)),
            'traits': get_astrological_traits(astrological)
        })

        return ret
