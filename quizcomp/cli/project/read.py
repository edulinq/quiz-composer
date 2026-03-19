"""
Read (an optionally save) a Quiz Composer project.
"""

import argparse
import sys

import quizcomp.cli.parser
import quizcomp.project

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    project = quizcomp.project.Project.from_path(args.path)

    quizzes, questions = project.load_resources()

    print(f"Found {len(quizzes)} quizzes.")
    for (path, quiz) in quizzes:
        print(f"    {path} ({quiz.title})")

    print(f"Found {len(questions)} question.")
    for (path, question) in questions:
        text = f"    {path}"
        if (question.name != ''):
            text += f" ({question.name})"

        print(text)

    if (args.out_dir is not None):
        project.save(args.out_dir)

    return 0

def main() -> int:
    """ Get a parser, parse the args, and call run. """

    return run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get the parser. """

    parser = quizcomp.cli.parser.get_parser(__doc__.strip())

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a project dir or config file.')

    parser.add_argument('--outdir', dest = 'out_dir',
        action = 'store', type = str, default = None,
        help = 'Save the project to this directory.')

    return parser

if (__name__ == '__main__'):
    sys.exit(main())
