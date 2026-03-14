"""
Create and upload a GradeScope PDF quiz.
"""

import argparse
import logging
import os
import sys

import edq.util.dirent
import edq.util.json

import quizcomp.cli.parser
import quizcomp.pdf
import quizcomp.uploader.gradescope

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    quiz, variants, options = quizcomp.pdf.make_with_args(args, write_options = False)
    out_dir = options['out_dir']

    options['gradescope'] = {
        'course': args.course_id,
        'rubric': args.rubric,
        'user': args.user,
    }

    gradescope_ids = []

    for i in range(len(variants)):
        variant = variants[i]

        uploader = quizcomp.uploader.gradescope.GradeScopeUploader(args.course_id, args.user, args.password,
                force = args.force, rubric = args.rubric,
                save_http = args.save_http)
        gradescope_id, created = uploader.upload_quiz(variant, base_dir = out_dir)

        options['variants'][i]['gradescope_id'] = gradescope_id

    # If there are multiple variants and all variants were created (non were skipped).
    if (len(variants) > 1):
        ids = [variants_data['gradescope_id'] for variants_data in options['variants']]

        uploader = quizcomp.uploader.gradescope.GradeScopeUploader(args.course_id, args.user, args.password,
                save_http = args.save_http)
        uploader.create_assignment_group(quiz.title, ids)
        logging.info("Created GradeScope Assignment Group: '%s'.", quiz.title)

    path = os.path.join(out_dir, quizcomp.pdf.OPTIONS_FILENAME)
    with open(path, 'w') as file:
        edq.util.json.dump(options, file, indent = 4)

    return 0

def main() -> int:
    """ Get a parser, parse the args, and call run. """

    return run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get the parser. """

    parser = quizcomp.cli.parser.get_parser(__doc__.strip(),
        include_net = True,
        include_latex = True,
    )

    quizcomp.pdf.modify_parser(parser)

    parser.add_argument('--rubric', dest = 'rubric',
        action = 'store_true', default = False,
        help = 'Create an initial rubric for this assignment in GradeScope (default: %(default)s).')

    parser.add_argument('--course', dest = 'course_id',
        action = 'store', type = str, required = True,
        help = 'Course ID to upload the quiz under.')

    parser.add_argument('--user', dest = 'user',
        action = 'store', type = str, required = True,
        help = 'The user to authenticate as.')

    parser.add_argument('--pass', dest = 'password',
        action = 'store', type = str, required = True,
        help = 'The password to use.')

    parser.add_argument('--force', dest = 'force',
        action = 'store_true', default = False,
        help = 'Override (delete) any exiting quiz with the same name (default: %(default)s).')

    parser.add_argument('--save-http', dest = 'save_http',
        action = 'store_true', default = False,
        help = 'Save any http requests to a debugging directory (default: %(default)s).')

    return parser

if (__name__ == '__main__'):
    sys.exit(main())
