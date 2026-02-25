import os
import sys

import quizcomp.args
import quizcomp.quiz
import quizcomp.uploader.canvas

DEFAULT_BASE_URL = 'https://canvas.ucsc.edu'

def run(args):
    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    quiz = quizcomp.quiz.Quiz.from_path(args.path)
    canvas_instance = quizcomp.uploader.canvas.InstanceInfo(args.base_url, args.course_id, args.token)

    uploader = quizcomp.uploader.canvas.CanvasUploader(canvas_instance, force = args.force)
    uploader.upload_quiz(quiz)

    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Parse a quiz and upload the quiz to Canvas.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz json file.')

    parser.add_argument('--course', dest = 'course_id',
        action = 'store', type = str, required = True,
        help = 'Course ID to upload the quiz under.')

    parser.add_argument('--url', dest = 'base_url',
        action = 'store', type = str, default = DEFAULT_BASE_URL,
        help = 'The base URL for the Canvas instance (default: %(default)s).')

    parser.add_argument('--token', dest = 'token',
        action = 'store', type = str, required = True,
        help = 'The authentication token to use with Canvas.')

    parser.add_argument('--force', dest = 'force',
        action = 'store_true', default = False,
        help = 'Override (delete) any exiting quiz with the same name.')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
