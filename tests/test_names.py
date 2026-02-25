import quizcomp.common
import quizcomp.group
import quizcomp.question.base
import tests.base

class NamesTest(tests.base.BaseTest):
    def setUp(self):
        super().setUp()
        self.valid_names = ["Week 1", "Group_A", "Q-1", "Intro.1"]
        self.invalid_names = ["Invalid/Name", "Name!", "Line\nBreak", "\tTabbed", " leading", "trailing "]

    def test_group_names_valid(self):
        dummy_question = quizcomp.question.base.Question.from_dict({
                'question_type': 'essay',
                'prompt': 'Test prompt.'
        })
        for name in self.valid_names:
            group = quizcomp.group.Group(name=name, pick_count=0, questions=[dummy_question])
            self.assertEqual(group.name, name)

    def test_group_names_invalid(self):
        dummy_question = quizcomp.question.base.Question.from_dict({
                'question_type': 'essay',
                'prompt': 'Test prompt.'
        })
        for name in self.invalid_names + [""]:
            with self.assertRaises(quizcomp.common.QuizValidationError):
                quizcomp.group.Group(name=name, pick_count=0, questions=[dummy_question])

    def test_question_names_valid(self):
        for name in self.valid_names + [""]:
            question = quizcomp.question.base.Question.from_dict({
                'question_type': 'essay',
                'name': name,
                'prompt': 'Test prompt.'
            })
            self.assertEqual(question.name, name)

    def test_question_names_invalid(self):
        for name in self.invalid_names:
            with self.assertRaises(quizcomp.common.QuizValidationError):
                quizcomp.question.base.Question.from_dict({
                    'question_type': 'essay',
                    'name': name,
                    'prompt': 'Test prompt.'
                })
