import typing

import quizcomp.common
import quizcomp.question.base
import quizcomp.quiz

DUMMY_QUIZ_DATA: typing.Dict[str, typing.Any] = {
    'title': 'Dummy Title',
    'description': 'Dummy description.',
    'course_title': 'Dummy Course',
    'term_title': 'Dummy Term',
    'version': '0.0.0',
}

DUMMY_GROUP_DATA: typing.Dict[str, typing.Any] = {
    'name': 'Dummy Question',
    'hints': {},
    'hints_first': {},
    'hints_last': {},
}

class Variant(quizcomp.quiz.Quiz):
    """
    A quiz varint is an instantiation of a quiz with specific set of questions chosen for each group.
    Variants still have question groups, but each group must only have the exact number of questions required for each group
    (or it is a validation error).

    Variants created directly from quizzes (as opposed to from a JSON file)
    will already have all the correct components, and will therefore only be lightly validated.
    Quizzes created from files will undergo full validation.
    """

    def __init__(self,
            type = quizcomp.constants.TYPE_VARIANT,
            **kwargs: typing.Any) -> None:
        super().__init__(type = type, **kwargs)
        self.validate(cls = Variant, **kwargs)

        self.questions = []
        for group in self.groups:
            self.questions += group.questions

    def _validate(self, **kwargs: typing.Any) -> None:
        """ Check if this variant is valid, will raise if the group is not valid. """

        # Ensure that each group has the correct number of questions.
        for i in range(len(self.groups)):
            group = self.groups[i]

            if (len(group.questions) != group.pick_count):
                raise quizcomp.common.QuizValidationError(
                        "Group at index {i} ('{group.name}') has {len(group.questions)} questions, expecting exactly {group.pick_count}.")

    @staticmethod
    def get_dummy(question: quizcomp.question.base.Question) -> 'Variant':
        """
        Get a "dummy" variant that has no real information.
        """

        quiz_data = DUMMY_QUIZ_DATA.copy()
        group_data = DUMMY_GROUP_DATA.copy()

        group_data['questions'] = [question]
        group_data['_skip_class_validations'] = [quizcomp.group.Group]
        quiz_data['groups'] = [quizcomp.group.Group(**group_data)]

        return Variant(**quiz_data)
