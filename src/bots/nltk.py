from typing import Optional

from nltk.chat import Chat
from nltk.chat.eliza import eliza_chatbot
from nltk.chat.iesha import iesha_chatbot
from nltk.chat.rude import rude_chatbot
from nltk.chat.suntsu import suntsu_chatbot
from nltk.chat.zen import zen_chatbot

from ..abstracts import Bot


class NLTKBot(Bot):
    def __init__(self, name: str, inst: Chat, sex: Optional[str] = None):
        self.inst = inst

        self._info = {
            'F': '[They:she][Them:her][Their:her][Theirs:hers]',
            'M': '[They:he][Them:him][Their:his][Theirs:his]'
        }.get(sex,
              '[They:they][Them:them][Their:their][Theirs:theirs]')

        self._info += '[Name:{}]'.format(name)

    def respond(self, text: str, **kwargs) -> str:
        return self.inst.respond(text)

    def info(self) -> str:
        return self._info


def ElizaBot():
    return NLTKBot('Eliza', eliza_chatbot, 'F')


def IeshaBot():
    return NLTKBot('Iesha',  iesha_chatbot, 'F')


def RudeBot():
    return NLTKBot('Eliza', rude_chatbot)


def SunTsuBot():
    return NLTKBot('Sun Tsu', suntsu_chatbot, 'M')


def ZenBot():
    return NLTKBot('Zen', zen_chatbot)
