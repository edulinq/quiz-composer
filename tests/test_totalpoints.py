import os

import quizcomp.quiz
import tests.base

class TestTotalPoints(tests.base.BaseTest):
    """
    Test the total_points method of the Quiz and Variant classes.
    """

    def test_single_question_points(self):
        path = os.path.join('tests', 'quizzes', 'good', 'single-question', 'quiz.json')
        quiz = quizcomp.quiz.Quiz.from_path(path)
        
        self.assertEqual(quiz.total_points(), 10, "Quiz blueprint should have 10 points")

    def test_variant_points(self):
        path = os.path.join('tests', 'quizzes', 'good', 'single-question', 'quiz.json')
        quiz = quizcomp.quiz.Quiz.from_path(path)
        
        variant = quiz.create_variant()
        self.assertEqual(variant.total_points(), 10, "Quiz variant should have 10 points")

    def test_all_basic_questions_points(self):
        path = os.path.join('tests', 'quizzes', 'good', 'all-basic-questions', 'quiz.json')
        quiz = quizcomp.quiz.Quiz.from_path(path)

        self.assertEqual(quiz.total_points(), 110)