from abc import abstractmethod


class Generator:
    @abstractmethod
    def generate_text(self, length: int):
        raise NotImplementedError()

    @abstractmethod
    def save_to_file(self, file_name: str, length: int):
        raise NotImplementedError()


class Bot(Generator):
    @abstractmethod
    def respond(self, text: str):
        raise NotImplementedError()
