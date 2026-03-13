"""
Parse a single quiz question (JSON file) and output the result in the specified format.
"""

import argparse
import os
import sys

import quizcomp.cli.parser
import quizcomp.converter.convert
import quizcomp.constants
import quizcomp.question.base

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    question = quizcomp.question.base.Question.from_path(args.path)
    content = quizcomp.converter.convert.convert_question(question, format = args.format,
            constructor_args = {'answer_key': args.answer_key})

    print(content)

    return 0

def main() -> int:
    """ Get a parser, parse the args, and call run. """

    return run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get the parser. """

    parser = quizcomp.cli.parser.get_parser(__doc__.strip(),
        include_katex = True,
    )

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz question json file.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizcomp.constants.FORMAT_JSON,
        choices = quizcomp.converter.convert.SUPPORTED_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    parser.add_argument('--key', dest = 'answer_key',
        action = 'store_true', default = False,
        help = 'Generate an answer key instead of a blank quiz (default: %(default)s).')

    return parser

if (__name__ == '__main__'):
    sys.exit(main())
