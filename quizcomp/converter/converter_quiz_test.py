import glob
import os
import typing

import quizcomp.converter.convert
import quizcomp.model.quiz
import quizcomp.testing.base

SEED: int = 0

class TestQuizConverter(quizcomp.testing.base.BaseTest):
    """
    Test converting all good quizzes to all supported formats.
    The content of the conversion is not tested, only that it successful and produces content.
    """

def _add_converter_tests() -> None:
    """ Add test cases for converting quizzes to all supported formats. """

    glob_path = os.path.join(quizcomp.testing.base.GOOD_QUIZZES_DIR, "**", quizcomp.model.constants.QUIZ_FILENAME)
    paths = sorted(glob.glob(glob_path, recursive = True))
    for path in paths:
        base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

        for format in quizcomp.converter.convert.SUPPORTED_FORMATS:
            for is_key in [True, False]:
                test_name = f"test_converter_quiz__{base_test_name}__{format.value}__key_{str(is_key).lower()}"
                setattr(TestQuizConverter, test_name, _get_template_test(path, format, is_key))

def _get_template_test(path: str, format: quizcomp.model.constants.Format, is_key: bool) -> typing.Callable:
    """ Get a test method for converting a quiz to a specific format. """

    def __method(self: TestQuizConverter) -> None:
        constructor_args = {'answer_key': is_key}

        quiz = self.load_quiz(path)
        variant = quiz.create_variant(all_questions = True, seed = SEED)
        content = quizcomp.converter.convert.convert_variant(
            variant,
            format = format,
            constructor_args = constructor_args,
        )

        self.assertTrue(len(content) > 10)

    return __method

_add_converter_tests()
