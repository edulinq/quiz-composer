import glob
import os
import re
import typing

import edq.util.json

import quizcomp.constants
import quizcomp.converter.convert
import quizcomp.quiz
import quizcomp.testing.base

EXPECTED_FILENAME: str = 'expected.json'

class TestTemplateConversion(quizcomp.testing.base.BaseTest):
    """
    Test template conversions.
    """

    def _assert_exists_replace(self, container: typing.Dict[str, typing.Any], key: str, replacement: typing.Any) -> typing.Any:
        """
        Ensure a value exists (and is not None), and then replace it.
        The old value will be returned.
        """

        value = container.get(key, None)
        self.assertIsNotNone(value, f"Key '{key}' does not exist.")

        container[key] = replacement

        return value

def _add_good_convert_questions() -> None:
    """ Add test cases for converting quizzes via templates. """

    glob_path = os.path.join(quizcomp.testing.base.GOOD_QUIZZES_DIR, "**", quizcomp.constants.QUIZ_FILENAME)
    paths = sorted(glob.glob(glob_path, recursive = True))
    for path in paths:
        test_name = _make_name('good_convert', path)
        setattr(TestTemplateConversion, test_name, _get_good_convert_test(path))

def _get_good_convert_test(path: str) -> typing.Callable:
    """ Get a test method for converting a good quiz. """

    def __method(self) -> None:
        base_dir = os.path.dirname(path)

        expected_path = os.path.join(base_dir, EXPECTED_FILENAME)
        if (not os.path.exists(expected_path)):
            self.fail(f"Expected quiz output does not exist: '{expected_path}'.")

        expected = edq.util.json.load_path(expected_path)

        quiz = quizcomp.quiz.Quiz.from_path(path)
        variant = quiz.create_variant()  # pylint: disable=no-member
        raw_result = quizcomp.converter.convert.convert_variant(variant, format = quizcomp.constants.FORMAT_JSON_TEMPLATE)

        result = edq.util.json.loads(raw_result)

        # Clean up the result.
        self._assert_exists_replace(result['quiz'], 'seed', 0)
        self._assert_exists_replace(result['quiz'], 'version', "test")

        # Clean up question base dirs specially by making them relative to the tests directory.
        for group in result['groups']:
            for question in group['questions']:
                base_dir = self._assert_exists_replace(question, 'base_dir', '')
                rel_dir = os.path.relpath(base_dir, quizcomp.testing.base.TESTDATA_DIR)
                question['base_dir'] = rel_dir

        # Convert the paths in the expected output to the system path separator.
        for group in expected.get('groups', []):
            for question in group['questions']:
                question['base_dir'] = os.path.join(*question['base_dir'].split('/'))

        self.assertJSONDictEqual(expected, result)

    return __method

def _add_bad_validate_questions() -> None:
    """ Add test cases for failing to convert quizzes. """

    glob_path = os.path.join(quizcomp.testing.base.BAD_QUIZZES_DIR, "**", quizcomp.constants.QUIZ_FILENAME)
    paths = sorted(glob.glob(glob_path, recursive = True))
    for path in paths:
        test_name = _make_name('bad_validate', path)
        setattr(TestTemplateConversion, test_name, _get_bad_validate_test(path))

def _get_bad_validate_test(path: str) -> typing.Callable:
    """ Get a test method for failing to ceate a quiz. """

    def __method(self) -> None:
        try:
            quizcomp.quiz.Quiz.from_path(path)
        except Exception:
            # Expected.
            return

        self.fail("Failed to raise an exception.")

    return __method

def _make_name(prefix: str, path: str) -> str:
    dirname = os.path.basename(os.path.dirname(path))
    dirname = quizcomp.testing.base.clean_name_part(dirname)

    return f"test_{prefix}__{dirname}"

def _apply_text_options(options: typing.Dict[str, typing.Any], a: str, b: str) -> typing.Tuple[str, str]:
    """ Apply a test option to text. """

    if (options.get("ignore-whitespace", False)):
        a = re.sub(r'\s+', '', a)
        b = re.sub(r'\s+', '', b)

    return a, b

_add_bad_validate_questions()
_add_good_convert_questions()
