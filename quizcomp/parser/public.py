"""
Pieces of the parsing infrastructure that are exposed for public use.
Code outside this package should generally only use these resources.
"""

import os

import quizcomp.common
import quizcomp.parser.common
import quizcomp.parser.parse
import quizcomp.util.serial
import quizcomp.util.dirent

class ParsedText(quizcomp.util.serial.PODSerializer):
    """
    A representation of text that has been successfully parsed.
    """

    def __init__(self, text, document):
        self.text = text
        self.document = document

    def to_pod(self, **kwargs):
        return self.text

def parse_text(text, base_dir = '.'):
    text, document = quizcomp.parser.parse._parse_text(text, base_dir)
    return ParsedText(text, document)

ALLOWED_LABEL_NODE_TYPES = {'inline', 'paragraph', 'root', 'softbreak', 'text'}

def parse_label(label, base_dir = '.'):
    if (isinstance(label, ParsedText)):
        return label

    if (label is None):
        label = ''

    text, document = quizcomp.parser.parse._parse_text(label, base_dir)
    _walk_label_ast(document.get_ast())
    return ParsedText(text, document)

def _walk_label_ast(node):
    node_type = node.get('type', '')

    if (node_type == 'container_block'):
        if (not node.get(quizcomp.parser.common.TOKEN_META_KEY_ROOT, False)):
            raise quizcomp.common.QuizValidationError(
                "Labels must be plain text (found '%s')." % (node_type))
    elif (node_type not in ALLOWED_LABEL_NODE_TYPES):
        raise quizcomp.common.QuizValidationError(
            "Labels must be plain text (found '%s')." % (node_type))

    for child in node.get('children', []):
        _walk_label_ast(child)

def parse_file(path):
    if (not os.path.isfile(path)):
        raise ValueError(f"Path to parse ('{path}') is not a file.")

    text = quizcomp.util.dirent.read_file(path)
    base_dir = os.path.dirname(path)

    return parse_text(text, base_dir = base_dir)
