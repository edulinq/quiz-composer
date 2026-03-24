"""
Pieces of the parsing infrastructure that are exposed for public use.
Code outside this package should generally only use these resources.
"""

import os
import typing

import edq.util.dirent

import quizcomp.model.text
import quizcomp.parser.document
import quizcomp.parser.render

def parse_text(text: str, base_dir: typing.Union[str, None] = None) -> quizcomp.model.text.ParsedText:
    """ Parse text with default options. """

    if (base_dir is None):
        base_dir = '.'

    text, tokens = quizcomp.parser.render._parse_text(text, base_dir)
    document = quizcomp.parser.document.ParsedDocument(tokens, base_dir = base_dir)

    return quizcomp.model.text.ParsedText(text, document)

def parse_file(raw_path: str, base_dir: typing.Union[str, None] = None) -> quizcomp.model.text.ParsedText:
    """ Parse a text file. """

    if (base_dir is None):
        base_dir = '.'

    # Prepend the base dir if the path is not absolute.
    if (not os.path.isabs(raw_path)):
        raw_path = os.path.join(base_dir, raw_path)

    path = os.path.abspath(raw_path)

    if (not os.path.isfile(path)):
        raise ValueError(f"Path to parse ('{raw_path}') does not exist or is not a file.")

    text = edq.util.dirent.read_file(path)
    base_dir = os.path.dirname(path)

    return parse_text(text, base_dir = base_dir)
