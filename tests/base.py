import glob
import os
import unittest

import quizcomp.constants
import quizcomp.parser.math
import quizcomp.util.json

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TESTS_DIR = THIS_DIR

QUESTIONS_DIR = os.path.join(TESTS_DIR, "questions")
GOOD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "good")
BAD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "bad")

DOCUMENTS_DIR = os.path.join(TESTS_DIR, 'documents')
GOOD_DOCUMENTS_DIR = os.path.join(DOCUMENTS_DIR, "good")
BAD_DOCUMENTS_DIR = os.path.join(DOCUMENTS_DIR, "bad")

QUIZZES_DIR = os.path.join(TESTS_DIR, 'quizzes')
GOOD_QUIZZES_DIR = os.path.join(QUIZZES_DIR, "good")
BAD_QUIZZES_DIR = os.path.join(QUIZZES_DIR, "bad")

DATA_DIR = os.path.join(TESTS_DIR, 'data')
COMMONMARK_TEST_DATA_PATH = os.path.join(DATA_DIR, 'commonmark_test_cases.json')

HTTP_SESSIONS_DIR = os.path.join(TESTS_DIR, "httpsessions")

class BaseTest(unittest.TestCase):
    # See full diffs regardless of size.
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        # Disable KaTeX for testing.
        quizcomp.parser.math._katex_available = False
        pass

    @classmethod
    def tearDownClass(cls):
        quizcomp.parser.math._katex_available = None
        pass

    def assertJSONDictEqual(self, expected, actual):
        expected_json = quizcomp.util.json.dumps(expected, indent = 4, sort_keys = True)
        actual_json = quizcomp.util.json.dumps(actual, indent = 4, sort_keys = True)

        message = f"\n---\nExpected: {expected_json}\n###\nActual: {actual_json}\n---\n"
        self.assertDictEqual(expected, actual, msg = message)

    def assertLongStringEqual(self, expected, actual):
        message = f"\n--- expected ---\n{expected}\n--- actual ---\n{actual}\n---\n"
        self.assertEqual(expected, actual, msg = message)

def discover_question_tests():
    good_paths = list(sorted(glob.glob(os.path.join(GOOD_QUESTIONS_DIR, "**", quizcomp.constants.QUESTION_FILENAME), recursive = True)))
    bad_paths = list(sorted(glob.glob(os.path.join(BAD_QUESTIONS_DIR, "**", quizcomp.constants.QUESTION_FILENAME), recursive = True)))

    return good_paths, bad_paths

def discover_good_document_files():
    return list(sorted(glob.glob(os.path.join(GOOD_DOCUMENTS_DIR, "**", "*.json"), recursive = True)))

def discover_bad_document_files():
    return list(sorted(glob.glob(os.path.join(BAD_DOCUMENTS_DIR, "**", "*.json"), recursive = True)))

def discover_good_quiz_files():
    return list(sorted(glob.glob(os.path.join(GOOD_QUIZZES_DIR, "**", quizcomp.constants.QUIZ_FILENAME), recursive = True)))

def discover_bad_quiz_files():
    return list(sorted(glob.glob(os.path.join(BAD_QUIZZES_DIR, "**", quizcomp.constants.QUIZ_FILENAME), recursive = True)))
