"""
Create a PDF from a single question.
"""

import sys

import quizcomp.args
import quizcomp.pdf

def run(args):
    quizcomp.pdf.make_question_with_path(args.path,
            out_dir = args.out_dir,
            answer_key = args.answer_key,
            skip_tex = args.skip_tex,
            skip_pdf = args.skip_pdf)
    return 0

def _get_parser():
    parser = quizcomp.args.Parser(description =
        "Create a PDF from a single question.")

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a question json file.')

    parser.add_argument('--outdir', dest = 'out_dir',
        action = 'store', type = str, default = '.',
        help = ('The directory to put the question PDF output.'
                + ' (default: %(default)s).'))

    parser.add_argument('--key', dest = 'answer_key',
        action = 'store_true', default = False,
        help = 'Create an answer key PDF (default: %(default)s).')

    parser.add_argument('--skip-tex', dest = 'skip_tex',
        action = 'store_true', default = False,
        help = 'Skip creating TeX files (default: %(default)s).')

    parser.add_argument('--skip-pdf', dest = 'skip_pdf',
        action = 'store_true', default = False,
        help = 'Skip compiling PDFs from TeX (default: %(default)s).')

    return parser

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
