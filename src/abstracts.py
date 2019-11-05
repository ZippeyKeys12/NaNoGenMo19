from abc import abstractmethod


class Generator:
    @abstractmethod
    def generate_text(self):
        raise NotImplementedError()

    @abstractmethod
    def save_to_file(self, name):
        raise NotImplementedError()


class Bot(Generator):
    @abstractmethod
    def respond(self, text: str):
        raise NotImplementedError()
