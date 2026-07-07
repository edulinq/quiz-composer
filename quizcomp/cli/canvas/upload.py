"""
Alias for `lms.cli.courses.quizzes.upload`.
"""

import argparse
import sys

import lms.cli.courses.quizzes.upload as alias

def main() -> int:
    """ Get a parser, parse the args, and call run. """

    return alias.run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get a parser for this operation. """

    parser = alias._get_parser()
    parser.epilog = __doc__.strip()
    return parser

if (__name__ == '__main__'):
    sys.exit(main())
