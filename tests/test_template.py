import os
import re

import edq.util.json

import quizcomp.constants
import quizcomp.converter.convert
import quizcomp.quiz
import tests.base

EXPECTED_FILENAME = 'expected.json'

class TestTemplateConversion(tests.base.BaseTest):
    """
    Test template conversion.
    """

    def _assert_exists_replace(self, container, key, replacement):
        """
        Ensure a value exists (and is not None), and then replace it.
        The old value will be returned.
        """

        value = container.get(key, None)
        self.assertIsNotNone(value, f"Key '{key}' does not exist.")

        container[key] = replacement

        return value

def _add_good_convert_questions():
    for quiz_path in tests.base.discover_good_quiz_files():
        test_name = _make_name('good_convert', quiz_path)
        setattr(TestTemplateConversion, test_name, _get_good_convert_test(quiz_path))

def _get_good_convert_test(quiz_path):
    """
    That that the tests here rely on the `quizcomp.converter.json.JSONTemplateConverter` converter.
    This is not meant for production use and may not have full functionality.
    The main difficulty it has is when converting answers to an easy format for testing.
    As more tests are developed, this conversion may need to be adjusted to better test different aspects,
    e.g., feedback is currently ignored when converting answers.
    """

    def __method(self):
        base_dir = os.path.dirname(quiz_path)
        name = os.path.basename(base_dir)

        expected_path = os.path.join(base_dir, EXPECTED_FILENAME)
        if (not os.path.exists(expected_path)):
            self.fail(f"Expected quiz output does not exist: '{expected_path}'.")

        expected = edq.util.json.load_path(expected_path)

        quizcomp.converter.convert

        quiz = quizcomp.quiz.Quiz.from_path(quiz_path)
        variant = quiz.create_variant()
        raw_result = quizcomp.converter.convert.convert_variant(variant, format = quizcomp.constants.FORMAT_JSON_TEMPLATE)

        result = edq.util.json.loads(raw_result)

        # Clean up the result.
        self._assert_exists_replace(result['quiz'], 'seed', 0)
        self._assert_exists_replace(result['quiz'], 'version', "test")

        # Clean up question base dirs specially by making them relative to the tests directory.
        for group in result['groups']:
            for question in group['questions']:
                base_dir = self._assert_exists_replace(question, 'base_dir', '')
                rel_dir = os.path.relpath(base_dir, tests.base.TESTS_DIR)
                question['base_dir'] = rel_dir

        # Convert the paths in the expected output to the system path separator.
        for group in expected.get('groups', []):
            for question in group['questions']:
                question['base_dir'] = os.path.join(*question['base_dir'].split('/'))

        self.assertJSONDictEqual(expected, result)

    return __method

def _add_bad_validate_questions():
    for quiz_path in tests.base.discover_bad_quiz_files():
        test_name = _make_name('bad_validate', quiz_path)
        setattr(TestTemplateConversion, test_name, _get_bad_validate_test(quiz_path))

def _get_bad_validate_test(quiz_path):
    def __method(self):
        try:
            quiz = quizcomp.quiz.Quiz.from_path(quiz_path)
        except Exception:
            # Expected.
            return

        self.fail("Failed to raise an exception.")

    return __method

def _make_name(prefix, path):
    dirname = os.path.basename(os.path.dirname(path))
    dirname = _clean_name_part(dirname)

    return "test_%s__%s" % (prefix, dirname)

def _clean_name_part(text):
    clean_text = text.lower().strip().replace(' ', '_')
    clean_text = re.sub(r'\W+', '', clean_text)
    return clean_text

def _apply_text_options(options, a, b):
    if (options.get("ignore-whitespace", False)):
        a = re.sub(r'\s+', '', a)
        b = re.sub(r'\s+', '', b)

    return a, b

_add_bad_validate_questions()
_add_good_convert_questions()
