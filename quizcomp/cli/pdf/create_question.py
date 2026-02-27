"""
Create a PDF from a single question.
"""

import sys

import quizcomp.args
import quizcomp.pdf

def run(args):
    quizcomp.pdf.make_from_question_with_args(args)
    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Create a PDF from a single question.")

    quizcomp.pdf.set_cli_question_args(parser)

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
