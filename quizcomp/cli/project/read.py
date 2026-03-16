"""
Read (an optionally save) a Quiz Composer project.
"""

import sys

import quizcomp.args
import quizcomp.project

def run(args):
    project = quizcomp.project.Project.from_path(args.path)

    quizzes, questions = project.load_resources()

    print("Found %d quizzes." % (len(quizzes)))
    for (path, quiz) in quizzes:
        print("    %s (%s)" % (path, quiz.title))

    print("Found %d question." % (len(questions)))
    for (path, question) in questions:
        text = "    %s" % (path)
        if (question.name.text != ''):
            text += " (%s)" % (question.name.text)

        print(text)

    if (args.out_dir is not None):
        project.save(args.out_dir)

    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        __doc__.strip())

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a project dir or config file.')

    parser.add_argument('--outdir', dest = 'out_dir',
        action = 'store', type = str, default = None,
        help = 'Save the project to this directory.')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
