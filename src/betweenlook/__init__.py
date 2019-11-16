from typing import List

from tracery import Grammar
from tracery.modifiers import base_english

from ..abstracts import Bot, Generator
from ..bots import ElizaBot
from ..util import word_count


class BetweenLookGenerator(Generator):
    def __init__(self, bot1: Bot, bot2: Bot):
        self.bot1 = bot1
        self.bot2 = bot2

        self.grammar = Grammar({
            'origin': ['{quote} #name# {verb}.',
                       # '{quote} {verb} #name#',
                       '#name# {verb}, {quote}'],
            'neutral': ['said'],
            'question': ['questioned', 'asked', 'inquired'],
            'exclaim': ['exclaimed', 'shouted'],
            'name': ['#They#', '#name#']
        })
        self.grammar.add_modifiers(base_english)

    def generate_text(self, **kwargs):
        length = kwargs.get('length', 50000)

        history: List[str] = [self.bot1.respond('')]
        w_count = word_count(history[0])

        quote = '"{}"'.format

        second = True
        while w_count < length:
            if second:
                sent = self.bot2.respond(history[-1])
                info = self.bot2.info()
            else:
                sent = self.bot1.respond(history[-1])
                info = self.bot1.info()

            second = not second

            history.append(sent)
            w_count += word_count(sent)

        text = ''

        for msg in history:
            msg = quote(msg)

            msg_type = 'neutral'
            if len(msg) >= 2:
                if msg[-2] == '?':
                    msg_type = 'question'

                elif msg[-2] == '!':
                    msg_type = 'exclaim'

            rule = self.grammar.flatten('\n{}#origin#'.format(info))
            rule = rule.format(quote=msg, verb='#{}#'.format(msg_type))
            rule = self.grammar.flatten(rule)

            text += rule[0].capitalize()+rule[1:]

        return text


def main():
    gen = BetweenLookGenerator(ElizaBot(), ElizaBot())

    text = gen.generate_text()

    with open('betweenlook.txt', 'w') as f:
        f.write(text)


if __name__ == "__main__":
    main()
