import re
import textwrap
from typing import Optional

from cytoolz.functoolz import pipe
from textacy.preprocessing import (normalize_hyphenated_words,
                                   normalize_quotation_marks,
                                   normalize_unicode, normalize_whitespace)

from .abstracts import Processor


class CleaningProcessor(Processor):
    clean_pattern = re.compile(r'[\n_]')

    def process_text(self, input_text: str, **kwargs) -> str:
        return pipe(
            input_text,
            lambda x: self.clean_pattern.sub(' ', x),
            normalize_hyphenated_words,
            normalize_quotation_marks,
            normalize_unicode,
            normalize_whitespace
        )


class TextWrapProcessor(Processor):
    def __init__(self, width: Optional[int] = None,
                 replace_whitespace: Optional[bool] = None):
        self.width = width
        self.replace_whitespace = replace_whitespace

    def process_text(self, input_text: str, **kwargs) -> str:
        width = kwargs.get('width', self.width or 70)

        repl_white = kwargs.get(
            'replace_whitespace', self.replace_whitespace or True)

        return '\n'.join(textwrap.wrap(
            input_text, width, replace_whitespace=repl_white))
