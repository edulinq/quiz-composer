import argparse
import logging
import os
import random
import traceback
import typing

import edq.util.dirent
import edq.util.json
import edq.util.time

import quizcomp.converter.tex
import quizcomp.external.latex
import quizcomp.model.question
import quizcomp.model.quiz

_logger = logging.getLogger(__name__)

OPTIONS_FILENAME: str = 'options.json'

def make_with_args(
        args: argparse.Namespace,
        **kwargs: typing.Any,
        ) -> typing.Tuple[quizcomp.model.quiz.Quiz, typing.List[quizcomp.model.quiz.Variant], typing.Dict[str, typing.Any]]:
    """
    Use a standard args object from set_cli_args() to make a PDF quiz.
    """

    if ((args.variants < 1) or (args.variants >= quizcomp.model.quiz.DEFAULT_MAX_VARIANTS)):
        raise ValueError(f"Number of variants must be in [1, {quizcomp.model.quiz.DEFAULT_MAX_VARIANTS}), found {args.variants}.")

    return make_with_path(args.path, base_out_dir = args.out_dir, seed = args.seed, num_variants = args.variants,
            skip_key = args.skip_key, skip_tex = args.skip_tex, skip_pdf = args.skip_pdf,
            **kwargs)

def make_with_path(
        quiz_path: str,
        **kwargs: typing.Any,
        ) -> typing.Tuple[quizcomp.model.quiz.Quiz, typing.List[quizcomp.model.quiz.Variant], typing.Dict[str, typing.Any]]:
    """ Make a PDF given the path to a quiz JSON. """

    if (not os.path.exists(quiz_path)):
        raise ValueError(f"Provided path '{quiz_path}' does not exist.")

    if (not os.path.isfile(quiz_path)):
        raise ValueError(f"Provided path '{quiz_path}' is not a file.")

    quiz = quizcomp.model.quiz.Quiz.from_path(quiz_path)
    return make(quiz, quiz_path = quiz_path, **kwargs)

def make_from_question_with_args(
        args: argparse.Namespace,
        **kwargs: typing.Any,
        ) -> typing.Tuple[quizcomp.model.quiz.Quiz, typing.List[quizcomp.model.quiz.Variant], typing.Dict[str, typing.Any]]:
    """
    Use a standard args object to make a PDF from a single question.
    """

    if ((args.variants < 1) or (args.variants >= quizcomp.model.quiz.DEFAULT_MAX_VARIANTS)):
        raise ValueError(f"Number of variants must be in [1, {quizcomp.model.quiz.DEFAULT_MAX_VARIANTS}), found {args.variants}.")

    return make_from_question_with_path(args.path,
            base_out_dir = args.out_dir, seed = args.seed, num_variants = args.variants,
            skip_key = args.skip_key, skip_tex = args.skip_tex, skip_pdf = args.skip_pdf,
            **kwargs)

def make_from_question_with_path(
        question_path: str,
        **kwargs: typing.Any,
        ) -> typing.Tuple[quizcomp.model.quiz.Quiz, typing.List[quizcomp.model.quiz.Variant], typing.Dict[str, typing.Any]]:
    """ Make a PDF given the path to a question JSON. """

    if (not os.path.exists(question_path)):
        raise ValueError(f"Provided path '{question_path}' does not exist.")

    if (not os.path.isfile(question_path)):
        raise ValueError(f"Provided path '{question_path}' is not a file.")

    question = quizcomp.model.question.Question.from_path(question_path)
    return make_from_question(question, **kwargs)

def make_from_question(
        question: quizcomp.model.question.Question,
        **kwargs: typing.Any,
        ) -> typing.Tuple[quizcomp.model.quiz.Quiz, typing.List[quizcomp.model.quiz.Variant], typing.Dict[str, typing.Any]]:
    """ Make a PDF given a question. """

    quiz = quizcomp.model.quiz.Variant.get_dummy(question)
    return make(quiz, **kwargs)

def make(
        quiz: quizcomp.model.quiz.Quiz,
        quiz_path: typing.Union[str, None] = None,
        base_out_dir: typing.Union[str, None] = None,
        seed: typing.Union[int, None] = None,
        num_variants: int = 1,
        write_options: bool = True,
        skip_key: bool = False,
        skip_tex: bool = False,
        skip_pdf: bool = False,
        **kwargs: typing.Any,
        ) -> typing.Tuple[quizcomp.model.quiz.Quiz, typing.List[quizcomp.model.quiz.Variant], typing.Dict[str, typing.Any]]:
    """ Make a PDF given a quiz. """

    if (base_out_dir is None):
        base_out_dir = edq.util.dirent.get_temp_path(prefix = 'quizcomp_pdf_', rm = False)

    out_dir = os.path.join(base_out_dir, quiz.get_name())
    edq.util.dirent.mkdir(out_dir)

    _logger.info("Writing TeX/PDF quiz ('%s') to '%s'.", quiz.get_name(), out_dir)

    if (seed is None):
        seed = random.randint(0, 2**64)

    now = edq.util.time.Timestamp.now()

    options = {
        'create_timestamp': now,
        'create_time': now.pretty(),
        'seed': seed,
        'out_dir': out_dir,
        'quiz': {
            'path': quiz_path,
            'name': quiz.get_name(),
            'version': quiz.version,
        },
    }

    # Options for each variant.
    variant_options = []

    _logger.debug("Using seed %d.", seed)

    variants = quiz.create_variants(count = num_variants, seed = seed)

    for (i, variant) in enumerate(variants):
        out_path = os.path.join(out_dir, f"{variant.get_name()}.json")
        variant.to_path(out_path)

        make_pdf(variant, out_dir = out_dir, is_key = False, skip_tex = skip_tex, skip_pdf = skip_pdf)

        name = variant.get_name()

        has_key = False
        if (not skip_key):
            try:
                variant.name = f"{name} -- Answer Key"
                make_pdf(variant, out_dir = out_dir, is_key = True, skip_tex = skip_tex, skip_pdf = skip_pdf)
                has_key = True
            except Exception:
                _logger.warning("Failed to generate answer key for '%s'.", name)
                _logger.debug(traceback.format_exc())
            finally:
                variant.name = name

        variant_options.append({
            'id': variant.variant_id,
            'name': name,
            'variant_index': i,
            'seed': seed,
            'has_key': has_key,
        })

        _logger.info("Completed variant: '%s'.", name)

    options['variants'] = variant_options

    if (write_options):
        path = os.path.join(out_dir, OPTIONS_FILENAME)
        edq.util.json.dump_path(options, path, indent = 4)

    return (quiz, variants, options)

def make_pdf(
        variant: quizcomp.model.quiz.Variant,
        out_dir: typing.Union[str, None] = None,
        is_key: bool = False,
        skip_tex: bool = False,
        skip_pdf: bool = False,
        ) -> str:
    """ Make a PDF given a quiz variant. """

    if (out_dir is None):
        out_dir = edq.util.dirent.get_temp_path(prefix = 'quizcomp_pdf_', rm = False)

    if (variant.variant_id is not None):
        out_dir = os.path.join(out_dir, f"Variant - {variant.variant_id}")

    edq.util.dirent.mkdir(out_dir)

    image_dir = os.path.join(out_dir, 'images')

    out_path = os.path.join(out_dir, f"{variant.get_name()}.tex")

    if (not skip_tex):
        converter = quizcomp.converter.tex.TexTemplateConverter(
            answer_key = is_key,
            image_base_dir = image_dir,
            cleanup_images = True,
        )
        content = converter.convert_variant(variant)

        edq.util.dirent.write_file(out_path, content)

    if (not skip_pdf):
        quizcomp.external.latex.compile(out_path)

    return out_dir

def modify_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """ Add PDF-based arguments to the CLI argument parser. """

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a JSON file.')

    parser.add_argument('--outdir', dest = 'out_dir',
        action = 'store', type = str, default = '.',
        help = 'The directory to put the output (default: %(default)s).')

    parser.add_argument('--skip-tex', dest = 'skip_tex',
        action = 'store_true', default = False,
        help = 'Skip creating TeX files (default: %(default)s).')

    parser.add_argument('--skip-pdf', dest = 'skip_pdf',
        action = 'store_true', default = False,
        help = 'Skip compiling PDFs from TeX (default: %(default)s).')

    parser.add_argument('--variants', dest = 'variants',
        action = 'store', type = int, default = 1,
        help = 'The number of quiz variants to create (default: %(default)s).')

    parser.add_argument('--skip-key', dest = 'skip_key',
        action = 'store_true', default = False,
        help = 'Skip creating the answer key (default: %(default)s).')

    parser.add_argument('--seed', dest = 'seed',
        action = 'store', type = int, default = None,
        help = 'The random seed to use (defaults to a random seed).')

    return parser
