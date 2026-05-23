import os
import re
import sys

import edq.testing.unittest
import edq.util.json

import quizcomp.model.question
import quizcomp.model.quiz
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

    _questions_cache: typing.Dict[str, quizcomp.model.question.Question] = {}
    """ A cache for loaded question filess, keyed by absolute path. """

    _quizzes_cache: typing.Dict[str, quizcomp.model.quiz.Quiz] = {}
    """ A cache for loaded quiz filess, keyed by absolute path. """

    @classmethod
    def setUpClass(cls) -> None:
        # Disable KaTeX for testing.
        quizcomp.parser.math._katex_available = False

    @classmethod
    def tearDownClass(cls) -> None:
        quizcomp.parser.math._katex_available = None

    def load_question(self, path: str) -> quizcomp.model.question.Question:
        """ Load a question from either the cache or disk. """

        path = os.path.abspath(path)

        if (path in self._questions_cache):
            return self._questions_cache[path]

        question = quizcomp.model.question.Question.from_path(path)
        self._questions_cache[path] = question

        return question

    def load_quiz(self, path: str) -> quizcomp.model.quiz.Quiz:
        """ Load a quiz from either the cache or disk. """

        path = os.path.abspath(path)

        if (path in self._quizzes_cache):
            return self._quizzes_cache[path]

        quiz = quizcomp.model.quiz.Quiz.from_path(path)
        self._quizzes_cache[path] = quiz

        return quiz

def clean_name_part(text: str) -> str:
    """ Clean a test name component. """

    clean_text = text.lower().strip().replace(' ', '_')
    clean_text = re.sub(r'\W+', '', clean_text)
    return clean_text
