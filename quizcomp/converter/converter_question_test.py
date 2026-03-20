import glob
import os
import typing

import quizcomp.converter.convert
import quizcomp.testing.base

class TestQuestionConverter(quizcomp.testing.base.BaseTest):
    """
    Test converting all good questions to all supported formats.
    The content of the conversion is not tested, only that it successful and produces content.
    """

    _question_cache: typing.Dict[str, quizcomp.question.base.Question] = {}
    """ Cache questions (by path) that have already been parased. """

    def _get_question(self, path: str) -> quizcomp.question.base.Question:
        """ Get a parsed question either from the cache or from disk. """

        path = os.path.abspath(path)
        if (path in TestQuestionConverter._question_cache):
            return TestQuestionConverter._question_cache[path]

        question = quizcomp.question.base.Question.from_path(path)
        TestQuestionConverter._question_cache[path] = question

        return question

def _add_converter_tests() -> None:
    """ Add test cases for converting questions to all supported formats. """

    glob_path = os.path.join(quizcomp.testing.base.GOOD_QUESTIONS_DIR, "**", quizcomp.constants.QUESTION_FILENAME)
    paths = sorted(glob.glob(glob_path, recursive = True))
    for path in paths:
        base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

        for format_name in quizcomp.converter.convert.SUPPORTED_FORMATS:
            for is_key in [True, False]:
                test_name = f"test_converter_question__{base_test_name}__{format_name}__key_{is_key}"
                setattr(TestQuestionConverter, test_name, _get_template_test(path, format_name, is_key))

def _get_template_test(path: str, format_name: str, is_key: bool) -> typing.Callable:
    """ Get a test method for converting a question to a specific format. """

    def __method(self) -> None:
        constructor_args = {'answer_key': is_key}

        question = self._get_question(path)
        content = quizcomp.converter.convert.convert_question(question, format = format_name,
                constructor_args = constructor_args)

        self.assertTrue(len(content) > 10)

    return __method

_add_converter_tests()
