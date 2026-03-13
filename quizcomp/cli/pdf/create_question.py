"""
Create a PDF from a single question.
"""

import argparse
import sys

import quizcomp.cli.parser
import quizcomp.pdf

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    quizcomp.pdf.make_from_question_with_args(args)
    return 0

def main() -> int:
    """ Get a parser, parse the args, and call run. """

    return run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get the parser. """

    parser = quizcomp.cli.parser.get_parser(__doc__.strip(),
        include_latex = True,
    )

    quizcomp.pdf.modify_parser(parser)

    return parser

if (__name__ == '__main__'):
    sys.exit(main())
