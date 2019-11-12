from nltk.chat import Chat
from nltk.chat.eliza import eliza_chatbot
from nltk.chat.iesha import iesha_chatbot
from nltk.chat.rude import rude_chatbot
from nltk.chat.suntsu import suntsu_chatbot
from nltk.chat.zen import zen_chatbot

from ..abstracts import Bot


class NLTKBot(Bot):
    def __init__(self, inst: Chat):
        self.inst = inst

    def respond(self, text: str, **kwargs) -> str:
        return self.inst.respond(text)


def ElizaBot():
    return NLTKBot(eliza_chatbot)


def IeshaBot():
    return NLTKBot(iesha_chatbot)


def RudeBot():
    return NLTKBot(rude_chatbot)


def SunTsuBot():
    return NLTKBot(suntsu_chatbot)


def ZenBot():
    return NLTKBot(zen_chatbot)
