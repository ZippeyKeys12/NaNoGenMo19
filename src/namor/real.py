from typing import Tuple

from faker import Faker as TruFaker
from faker.providers import person

from .abstracts import Namor


class RealNamor(Namor):
    def __init__(self):
        self.faker = TruFaker()
        self.faker.add_provider(person)

    def generate_name(self, sex: str) -> Tuple[str, str]:
        if sex == 'F':
            return (self.faker.first_name_female(),
                    self.faker.last_name_female())

        if sex == 'M':
            return (self.faker.first_name_male(),
                    self.faker.last_name_male())

        return (self.faker.first_name(), self.faker.last_name())
