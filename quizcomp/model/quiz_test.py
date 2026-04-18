import os

import quizcomp.quiz
import quizcomp.testing.base

class QuizTest(quizcomp.testing.base.BaseTest):
    """
    Test base functionally of quizzes.
    """

    def test_get_available_points_base(self) -> None:
        """ Test that quizzes have the correct number of total points. """

        # [(path, expected total), ...]
        test_cases = [
            (
                os.path.join(quizcomp.testing.base.GOOD_QUIZZES_DIR, 'single-question', 'quiz.json'),
                10,
            ),
            (
                os.path.join(quizcomp.testing.base.GOOD_QUIZZES_DIR, 'all-basic-questions', 'quiz.json'),
                110,
            ),
        ]

        for (i, test_case) in enumerate(test_cases):
            (path, expected) = test_case

            with self.subTest(msg = f"Case {i}: {path}"):
                quiz = quizcomp.quiz.Quiz.from_path(path)
                variant = quiz.create_variant()  # pylint: disable=no-member

                self.assertEqual(quiz.get_available_points(), expected, "quiz")  # pylint: disable=no-member
                self.assertEqual(variant.get_available_points(), expected, "variant")
