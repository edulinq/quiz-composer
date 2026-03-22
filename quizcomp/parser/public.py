"""
Pieces of the parsing infrastructure that are exposed for public use.
Code outside this package should generally only use these resources.
"""

import os

import edq.util.dirent

import quizcomp.model.text
import quizcomp.parser.document
import quizcomp.parser.render

def parse_text(text: str, base_dir: str = '.') -> quizcomp.model.text.ParsedText:
    """ Parse text with default options. """

    text, tokens = quizcomp.parser.render._parse_text(text, base_dir)
    document = quizcomp.parser.document.ParsedDocument(tokens, base_dir = base_dir)

    return quizcomp.model.text.ParsedText(text, document)

def parse_file(path: str) -> quizcomp.model.text.ParsedText:
    """ Parse a text file. """

    if (not os.path.isfile(path)):
        raise ValueError(f"Path to parse ('{path}') is not a file.")

    text = edq.util.dirent.read_file(path)
    base_dir = os.path.dirname(path)

    return parse_text(text, base_dir = base_dir)
