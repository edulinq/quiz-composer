"""
Parse a single file and output the results of the parse.
"""

import argparse
import sys

import quizcomp.cli.parser
import quizcomp.model.constants
import quizcomp.parser.document

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    document = quizcomp.parser.document.ParsedDocument.parse_file(args.path)

    content = document.to_format(quizcomp.model.constants.Format(args.format), pretty = True)
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
        help = 'The path to parse.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizcomp.model.constants.Format.JSON,
        choices = [choice.value for choice in quizcomp.model.constants.PARSER_FORMATS],
        help = 'Output the parsed document in this format (default: %(default)s).')

    return parser

if (__name__ == '__main__'):
    sys.exit(main())
