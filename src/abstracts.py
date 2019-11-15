from __future__ import annotations

from abc import abstractmethod
from typing import Dict


class Generator:
    @abstractmethod
    def generate_text(self, **kwargs) -> str:
        raise NotImplementedError()


class Processor:
    @abstractmethod
    def process_text(self, input_text: str, **kwargs) -> str:
        raise NotImplementedError()

    def __lshift__(self, other: Processor) -> Processor:
        if not isinstance(other, Processor):
            raise TypeError('Can only compose with objects of type Processor')

        return ComposedProcessor(other, self)

    def __rshift__(self, other: Processor) -> Processor:
        if not isinstance(other, Processor):
            raise TypeError('Can only compose with objects of type Processor')

        return ComposedProcessor(self, other)

    def __rrshift__(self, other: str) -> str:
        if not isinstance(other, str):
            raise TypeError(
                'Only strings can be passed into objects of type Processor')

        return self.process_text(other)


class ComposedProcessor(Processor):
    def __init__(self, one: Processor, two: Processor):
        self.one: Processor = one
        self.two: Processor = two

    def process_text(self, input_text, **kwargs):
        return self.two.process_text(self.one.process_text(input_text))


class Bot:
    @abstractmethod
    def info(self) -> Dict[str, str]:
        raise NotImplementedError()

    @abstractmethod
    def respond(self, text: str, **kwargs) -> str:
        raise NotImplementedError()
