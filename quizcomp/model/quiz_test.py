import copy
import glob
import os
import typing

import edq.util.json
import edq.util.serial

import quizcomp.constants
import quizcomp.model.errors
import quizcomp.model.quiz
import quizcomp.testing.base

SERIAL_FILENAME: str = 'serial.json'

class QuizTest(quizcomp.testing.base.BaseTest):
    """
    Test base functionally of quizzes.
    """

    def test_get_points_base(self) -> None:
        """ Test that quizzes have the correct number of total points. """

        # [(path, expected total), ...]
        test_cases = [
            (
                os.path.join(quizcomp.testing.base.GOOD_QUIZZES_DIR, 'simple', 'quiz.json'),
                0.0,
            ),
            (
                os.path.join(quizcomp.testing.base.GOOD_QUIZZES_DIR, 'all-basic-questions', 'quiz.json'),
                12.0,
            ),
        ]

        for (i, test_case) in enumerate(test_cases):
            (path, expected) = test_case

            with self.subTest(msg = f"Case {i}: {path}"):
                quiz = self.load_quiz(path)
                variant = quiz.create_variants()[0]

                self.assertEqual(quiz.get_points(), expected, "quiz")  # pylint: disable=no-member
                self.assertEqual(variant.get_points(), expected, "variant")

def _add_quiz_tests() -> None:
    """ Add test cases for parsing good and bad quizes. """

    good_glob_path = os.path.join(quizcomp.testing.base.GOOD_QUIZZES_DIR, "**", quizcomp.constants.QUIZ_FILENAME)
    good_paths = sorted(glob.glob(good_glob_path, recursive = True))
    for path in good_paths:
        try:
            _add_good_quiz_test(path)
        except Exception as ex:
            raise ValueError(f"Failed to parse good test case '{path}'.") from ex

    bad_glob_path = os.path.join(quizcomp.testing.base.BAD_QUIZZES_DIR, "**", quizcomp.constants.QUIZ_FILENAME)
    bad_paths = sorted(glob.glob(bad_glob_path, recursive = True))
    for path in bad_paths:
        try:
            _add_bad_quiz_test(path)
        except Exception as ex:
            raise ValueError(f"Failed to parse failing test case '{path}'.") from ex

def _add_good_quiz_test(path: str) -> None:
    """ Add test cases for parsing a good quiz. """

    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

    test_name = 'test_quiz_parse_' + base_test_name
    setattr(QuizTest, test_name, _get_quiz_parse_test_method(path))

    test_name = 'test_quiz_reparse_' + base_test_name
    setattr(QuizTest, test_name, _get_quiz_reparse_test_method(path))

    serial_path = os.path.join(os.path.dirname(path), SERIAL_FILENAME)
    if (os.path.exists(serial_path)):
        test_name = 'test_quiz_serial_' + base_test_name
        setattr(QuizTest, test_name, _get_quiz_serial_test_method(path, serial_path))

def _get_quiz_parse_test_method(path: str) -> typing.Callable:
    """ Get a test for just parsing a quiz file. """

    def __method(self: QuizTest) -> None:
        quiz = self.load_quiz(path)
        self.assertIsNotNone(quiz)

    return __method

def _get_quiz_reparse_test_method(path: str) -> typing.Callable:
    """ Get a test for parsing a quiz file, converting the quiz to a dict, then re-parsing the same quiz. """

    def __method(self: QuizTest) -> None:
        quiz = self.load_quiz(path)
        quiz_data = quiz.to_pod()

        new_quiz = quizcomp.model.quiz.Quiz.from_pod(copy.deepcopy(quiz_data), edq.util.serial.SerializationContext())
        new_quiz_data = new_quiz.to_pod()  # pylint: disable=no-member

        self.assertJSONDictEqual(quiz_data, new_quiz_data)

    return __method

def _get_quiz_serial_test_method(path: str, serial_path: str) -> typing.Callable:
    """ Get a test for parsing a quiz, converting it to a dict, and checking that dict against a given file. """

    def __method(self: QuizTest) -> None:
        quiz = self.load_quiz(path)
        actual_data = quiz.to_pod()

        expected_data = edq.util.json.load_path(serial_path)

        self.assertJSONDictEqual(expected_data, actual_data)

    return __method

def _add_bad_quiz_test(path: str) -> None:
    """ Add a test case for parsing a bad quiz. """

    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

    test_name = 'test_quiz_bad_' + base_test_name
    setattr(QuizTest, test_name, _get_quiz_bad_test_method(path))

def _get_quiz_bad_test_method(path: str) -> typing.Callable:
    """ Get a test for failing to parse a quiz. """

    def __method(self: QuizTest) -> None:
        with self.assertRaises(quizcomp.model.errors.QuizValidationError):
            self.load_quiz(path)

    return __method

_add_quiz_tests()
