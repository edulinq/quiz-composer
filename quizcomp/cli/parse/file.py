import sys

import quizcomp.args
import quizcomp.constants
import quizcomp.parser.public

def run(args):
    document = quizcomp.parser.public.parse_file(args.path).document

    content = document.to_format(args.format, pretty = True)
    print(content)

    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Parse a single file and output the results of the parse.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to parse.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizcomp.constants.FORMAT_JSON,
        choices = quizcomp.constants.PARSER_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
