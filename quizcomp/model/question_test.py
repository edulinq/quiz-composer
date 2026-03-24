import glob
import os
import typing

import edq.util.json

import quizcomp.common
import quizcomp.constants
import quizcomp.model.question
import quizcomp.uploader.canvas
import quizcomp.testing.base

CANVAS_FILENAME: str = 'canvas.json'
SERIAL_FILENAME: str = 'serial.json'

CANVAS_TEST_GROUP_ID: int = 0
CANVAS_TEST_INDEX: int = 0

_test_canvas_instance: quizcomp.uploader.canvas.InstanceInfo = quizcomp.uploader.canvas.InstanceInfo(
    base_url = 'http://127.0.0.1:3030',
    course_id = '123',
    token = 'abc123',
    testing = True,
)

class QuestionsTest(quizcomp.testing.base.BaseTest):
    """
    Test parsing/generating all questions in the 'testsdata/questions/good' directory.
    A 'question.json' indicates a question that should be parsed.
    A 'canvas.json' in the same directory indicates that the question
    should also be checked for it's Canvas format.

    Test that questions in 'testsdata/questions/bad' do not parse.
    """

    _questions_cache: typing.Dict[str, quizcomp.model.question.Question] = {}

    def load_question(self, path: str) -> quizcomp.model.question.Question:
        """ Load a question from either the cache or disk. """

        path = os.path.abspath(path)

        if (path in self._questions_cache):
            return self._questions_cache[path]

        question = quizcomp.model.question.Question.from_path(path)
        self._questions_cache[path] = question

        return question

def _add_question_tests() -> None:
    """ Add test cases for parsing good and bad questions. """

    good_glob_path = os.path.join(quizcomp.testing.base.GOOD_QUESTIONS_DIR, "**", quizcomp.constants.QUESTION_FILENAME)
    good_paths = sorted(glob.glob(good_glob_path, recursive = True))
    for path in good_paths:
        try:
            _add_good_question_test(path)
        except Exception as ex:
            raise ValueError(f"Failed to parse good test case '{path}'.") from ex

    bad_glob_path = os.path.join(quizcomp.testing.base.BAD_QUESTIONS_DIR, "**", quizcomp.constants.QUESTION_FILENAME)
    bad_paths = sorted(glob.glob(bad_glob_path, recursive = True))
    for path in bad_paths:
        try:
            _add_bad_question_test(path)
        except Exception as ex:
            raise ValueError(f"Failed to parse failing test case '{path}'.") from ex

def _add_good_question_test(path: str) -> None:
    """ Add test cases for parsing a good question. """

    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

    test_name = 'test_question_parse_' + base_test_name
    setattr(QuestionsTest, test_name, _get_question_parse_test_method(path))

    test_name = 'test_question_reparse_' + base_test_name
    setattr(QuestionsTest, test_name, _get_question_reparse_test_method(path))

    canvas_path = os.path.join(os.path.dirname(path), CANVAS_FILENAME)
    if (os.path.exists(canvas_path)):
        test_name = 'test_question_canvas_' + base_test_name
        setattr(QuestionsTest, test_name, _get_question_canvas_test_method(path, canvas_path))

    json_path = os.path.join(os.path.dirname(path), SERIAL_FILENAME)
    if (os.path.exists(json_path)):
        test_name = 'test_question_serial_' + base_test_name
        setattr(QuestionsTest, test_name, _get_question_serial_test_method(path, json_path))

def _get_question_parse_test_method(path: str) -> typing.Callable:
    """ Get a test for just parsing a question file. """

    def __method(self: QuestionsTest) -> None:
        question = self.load_question(path)
        self.assertIsNotNone(question)

    return __method

def _get_question_reparse_test_method(path: str) -> typing.Callable:
    """ Get a test for parsing a question file, converting the question to a dict, then re-parsing the same question. """

    def __method(self: QuestionsTest) -> None:
        question = self.load_question(path)
        question_data = question.to_dict()

        new_question = quizcomp.model.question.Question.from_dict(question_data)
        new_question_data = new_question.to_dict()

        self.assertJSONDictEqual(question_data, new_question_data)

    return __method

def _get_question_canvas_test_method(path: str, canvas_path: str) -> typing.Callable:
    """ Get a test for reprsenting a question in a Canvas API format. """

    def __method(self: QuestionsTest) -> None:
        question = self.load_question(path)
        canvas_info = quizcomp.uploader.canvas._create_question_json(CANVAS_TEST_GROUP_ID, question, CANVAS_TEST_INDEX, _test_canvas_instance)

        expected_canvas_info = edq.util.json.load_path(canvas_path)

        self.assertJSONDictEqual(expected_canvas_info, canvas_info)

    return __method

def _get_question_serial_test_method(path: str, serial_path: str) -> typing.Callable:
    """ Get a test for parsing a question, converting it to a dict, and checking that dict against a given file. """

    def __method(self: QuestionsTest) -> None:
        question = self.load_question(path)
        actual_data = question.to_dict()

        expected_data = edq.util.json.load_path(serial_path)

        self.assertJSONDictEqual(expected_data, actual_data)

    return __method

def _add_bad_question_test(path: str) -> None:
    """ Add a test case for parsing a bad question. """

    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

    test_name = 'test_question_bad_' + base_test_name
    setattr(QuestionsTest, test_name, _get_question_bad_test_method(path))

def _get_question_bad_test_method(path: str) -> typing.Callable:
    """ Get a test for failing to parse a question. """

    def __method(self: QuestionsTest) -> None:
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.model.question.Question.from_path(path)

    return __method

_add_question_tests()
