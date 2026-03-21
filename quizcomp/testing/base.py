import os
import re
import sys

import edq.testing.unittest
import edq.util.json

import quizcomp.parser.math

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TESTDATA_DIR: str = os.path.join(THIS_DIR, '..', 'testdata')

QUESTIONS_DIR = os.path.join(TESTDATA_DIR, "questions")
GOOD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "good")
BAD_QUESTIONS_DIR = os.path.join(QUESTIONS_DIR, "bad")

QUIZZES_DIR = os.path.join(TESTDATA_DIR, "quizzes")
GOOD_QUIZZES_DIR = os.path.join(QUIZZES_DIR, "good")
BAD_QUIZZES_DIR = os.path.join(QUIZZES_DIR, "bad")

class BaseTest(edq.testing.unittest.BaseTest):
    """
    Test parsing text.
    Good and bad situations will be loaded from files into individual test methods.
    """

    @classmethod
    def setUpClass(cls) -> None:
        # Disable KaTeX in Windows for testing.
        if (sys.platform.startswith("win")):
            quizcomp.parser.math._katex_available = False

    @classmethod
    def tearDownClass(cls) -> None:
        quizcomp.parser.math._katex_available = None

def clean_name_part(text: str) -> str:
    """ Clean a test name component. """

    clean_text = text.lower().strip().replace(' ', '_')
    clean_text = re.sub(r'\W+', '', clean_text)
    return clean_text
