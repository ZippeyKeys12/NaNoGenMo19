from abc import abstractmethod
from typing import Tuple


class Namor:
    @abstractmethod
    def generate_name(self, sex: str) -> Tuple[str, str]:
        raise NotImplementedError()
