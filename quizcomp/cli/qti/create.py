import os
import sys

import quizcomp.args
import quizcomp.converter.qti
import quizcomp.quiz
import quizcomp.util.cli

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    quiz = quizcomp.quiz.Quiz.from_path(args.path)

    out_path = quizcomp.util.cli.resolve_out_arg(args.out, f'{quiz.title}.qti.zip')

    converter = quizcomp.converter.qti.QTITemplateConverter(canvas = args.canvas)
    converter.convert_quiz(quiz, out_path = out_path)

    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Parse a quiz and upload the quiz to Canvas.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz JSON file.')

    parser.add_argument('--canvas', dest = 'canvas',
        action = 'store_true', default = False,
        help = 'Create the QTI with Canvas-specific tweaks (default: %(default)s).')

    quizcomp.util.cli.add_out_arg(parser, '<title>.qti.zip')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
