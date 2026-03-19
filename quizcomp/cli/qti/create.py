"""
Parse a quiz and upload the quiz to Canvas.
"""

import argparse
import os
import sys

import quizcomp.cli.parser
import quizcomp.converter.qti
import quizcomp.pdf
import quizcomp.quiz

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    quiz = quizcomp.quiz.Quiz.from_path(args.path)

    out_path = quizcomp.cli.parser.resolve_out_arg(args.out, f'{quiz.title}.qti.zip')  # pylint: disable=no-member

    converter = quizcomp.converter.qti.QTITemplateConverter(canvas = args.canvas)
    converter.convert_quiz(quiz, out_path = out_path)

    return 0

def main() -> int:
    """ Get a parser, parse the args, and call run. """

    return run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get the parser. """

    parser = quizcomp.cli.parser.get_parser(__doc__.strip())

    parser.add_argument('--canvas', dest = 'canvas',
        action = 'store_true', default = False,
        help = 'Create the QTI with Canvas-specific tweaks (default: %(default)s).')

    quizcomp.cli.parser.add_out_arg(parser, '<title>.qti.zip')

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz JSON file.')

    return parser

if (__name__ == '__main__'):
    sys.exit(main())
