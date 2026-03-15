import os
import random
import sys

import quizcomp.args
import quizcomp.converter.convert
import quizcomp.constants
import quizcomp.quiz

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    seed = args.seed
    if (seed is None):
        seed = random.randint(0, 2**64)

    quiz = quizcomp.quiz.Quiz.from_path(args.path, flatten_groups = args.flatten_groups)
    variant = quiz.create_variant(all_questions = args.flatten_groups, seed = seed)
    content = quizcomp.converter.convert.convert_variant(variant, format = args.format,
            constructor_args = {'answer_key': args.answer_key})

    print(content)

    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Parse a single quiz and output the results of the parse.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz json file.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizcomp.constants.FORMAT_JSON,
        choices = quizcomp.converter.convert.SUPPORTED_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    parser.add_argument('--key', dest = 'answer_key',
        action = 'store_true', default = False,
        help = 'Generate an answer key instead of a blank quiz (default: %(default)s).')

    parser.add_argument('--flatten-groups', dest = 'flatten_groups',
        action = 'store_true', default = False,
        help = 'Flatten question groups with multiple questions to multiple groups with a single question (default: %(default)s).')

    parser.add_argument('--seed', dest = 'seed',
        action = 'store', type = int, default = None,
        help = 'The random seed to use (defaults to a random seed).')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
