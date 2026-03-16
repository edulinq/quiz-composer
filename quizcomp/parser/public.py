"""
Pieces of the parsing infrastructure that are exposed for public use.
Code outside this package should generally only use these resources.
"""

import os
import typing

import edq.util.dirent

import quizcomp.parser.document
import quizcomp.parser.parse
import quizcomp.util.serial

class ParsedText(quizcomp.util.serial.PODSerializer):
    """
    A representation of text that has been successfully parsed.
    """

    def __init__(self, text: str, document: quizcomp.parser.document.ParsedDocument):
        self.text: str = text
        """ The cleaned text that was parsed. """

        self.document = document
        """ The output of parsing. """

    def to_pod(self, **kwargs: typing.Any) -> quizcomp.util.serial.POD:
        return self.text

def parse_text(text: str, base_dir: str = '.') -> ParsedText:
    """ Parse text with default options. """

    text, document = quizcomp.parser.parse._parse_text(text, base_dir)
    return ParsedText(text, document)

def parse_file(path: str) -> ParsedText:
    """ Parse a text file. """

    if (not os.path.isfile(path)):
        raise ValueError(f"Path to parse ('{path}') is not a file.")

    text = edq.util.dirent.read_file(path)
    base_dir = os.path.dirname(path)

    return parse_text(text, base_dir = base_dir)
