import os

import quizcomp.common
import quizcomp.question.base
import quizcomp.uploader.canvas
import quizcomp.util.json
import tests.base

CANVAS_FILENAME = 'canvas.json'

CANVAS_TEST_GROUP_ID = 0
CANVAS_TEST_INDEX = 0

class QuestionsTest(tests.base.BaseTest):
    """
    Test parsing/generating all questions in the 'tests/questions/good' directory.
    A 'question.json' indicates a question that should be parsed.
    A 'canvas.json' in the same directory indicates that the question
    should also be checked for it's Canvas format.

    Test that questions in 'tests/questions/bad' do not parse.
    """

    pass

def _add_question_tests():
    good_paths, bad_paths = tests.base.discover_question_tests()

    for path in good_paths:
        try:
            _add_question_test(path)
        except Exception as ex:
            raise ValueError("Failed to parse test case '%s'." % (path)) from ex

    for path in bad_paths:
        try:
            _add_fail_question_test(path)
        except Exception as ex:
            raise ValueError("Failed to parse failing test case '%s'." % (path)) from ex

def _add_question_test(path):
    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

    test_name = 'test_question_parse_' + base_test_name
    setattr(QuestionsTest, test_name, _get_question_parse_test_method(path))

    test_name = 'test_question_reparse_' + base_test_name
    setattr(QuestionsTest, test_name, _get_question_reparse_test_method(path))

    canvas_path = os.path.join(os.path.dirname(path), CANVAS_FILENAME)
    if (os.path.exists(canvas_path)):
        test_name = 'test_question_canvas_' + base_test_name
        setattr(QuestionsTest, test_name, _get_question_canvas_test_method(path, canvas_path))

def _get_question_parse_test_method(path):
    """
    Get a test for just parsing a question file.
    """

    def __method(self):
        question = quizcomp.question.base.Question.from_path(path)
        self.assertIsNotNone(question)

    return __method

def _get_question_reparse_test_method(path):
    """
    Get a test for parsing a question file, converting the question to a dict, then re-parsing the same question.
    """

    def __method(self):
        question = quizcomp.question.base.Question.from_path(path)
        question_data = question.to_dict()

        new_question = quizcomp.question.base.Question.from_dict(question_data)
        new_question_data = new_question.to_dict()

        self.assertJSONDictEqual(question_data, new_question_data)

    return __method

def _get_question_canvas_test_method(path, canvas_path):
    def __method(self):
        question = quizcomp.question.base.Question.from_path(path)
        canvas_info = quizcomp.uploader.canvas._create_question_json(CANVAS_TEST_GROUP_ID, question, CANVAS_TEST_INDEX)

        with open(canvas_path, 'r') as file:
            expected_canvas_info = quizcomp.util.json.load(file)

        self.assertJSONDictEqual(expected_canvas_info, canvas_info)

    return __method

def _add_fail_question_test(path):
    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

    test_name = 'test_question_fail_' + base_test_name
    setattr(QuestionsTest, test_name, _get_question_fail_test_method(path))

def _get_question_fail_test_method(path):
    def __method(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.question.base.Question.from_path(path)

    return __method

_add_question_tests()
