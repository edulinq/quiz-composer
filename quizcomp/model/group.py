import glob
import logging
import os
import random
import typing

import quizcomp.common
import quizcomp.constants
import quizcomp.model.base
import quizcomp.question.base
import quizcomp.util.serial

DEFAULT_PICK_COUNT: int = 1
""" The default number of questions chosen from this group. """

DEFAULT_PICK_WITH_REPLACEMENT: bool = True
"""
The default replacement behavior between variants.
True means that different variants can have the same questions.
False means that they cannot, but can also cause a warning if not enough questions are available in a group.
"""

class Group(quizcomp.model.base.CoreType):
    """
    A group/bank of questions for a quiz.
    Questions can be grouped together and then a subset can be randomly chosen to create variety in quizzes.
    """

    # TEST - pick_with_replacement should be allowed at the quiz level.

    serialization_alias_fields = [
        # TEST
        # ('children', 'questions'),
    ]

    def __init__(self,
            questions: typing.Union[typing.List[quizcomp.model.question.Question], None] = None,
            pick_count: int = DEFAULT_PICK_COUNT,
            pick_with_replacement: bool = DEFAULT_PICK_WITH_REPLACEMENT,
            **kwargs: typing.Any) -> None:
        super().__init__(children = questions, **kwargs)

        if (pick_count < 0):
            raise quizcomp.common.QuizValidationError(f"Pick count must be non-negative, found: {pick_count}.", base_dir = base_dir)

        self.pick_count: int = pick_count
        """ The number of questions to choose from this group. """

        self.pick_with_replacement: bool = pick_with_replacement
        """
        Whether or not questions are chosen with replacement between variants.
        Choosing with replacement means that the same question may appear in multiple variants.
        """

        if (self.pick_count > len(self.children)):
            logging.warning("Group '%s' was asked to pick more questions than available (pick count: %d, group size: %d).",
                    self.name, self.pick_count, len(self.children))
            self.pick_count = len(self.children)

    def choose_variant_questions(self,
            all_questions: bool,
            with_replacement: bool,
            used_question_indexes: typing.Set[int],
            rng: random.Random,
            ) -> typing.List[quizcomp.question.base.Question]:
        """
        Get a list of questions to use for an instantiated variant of this group.
        The returned questions will be copies of the original and shuffled (it set in config).
        """

        if ((self.pick_count == 0) or (len(self.children) == 0)):
            logging.warning("Group '%s' will select no questions (pick_count: %d, group size: %d).",
                    self.name, self.pick_count, len(self.children))
            return []

        # TEST
        with_replacement = (self.pick_with_replacement and with_replacement)

        count = self.pick_count
        if (all_questions):
            count = len(self.children)

        questions = self._choose_questions(count, with_replacement, used_question_indexes, rng)

        # Rename questions if there are more than one.
        if (len(questions) > 1):
            for (i, question) in enumerate(questions):
                question.name = f"{self.name} - {i + 1}"

        return questions

    def _choose_questions(self,
            count: int,
            with_replacement: bool
            used_question_indexes: typing.Set[int],
            rng: random.Random,
            ) -> typing.List[quizcomp.question.base.Question]:
        """ Internally, choose a list of questions to use for an instantiated variant of this group. """

        indexes = list(range(len(self.children)))

        if (not with_replacement):
            indexes = list(set(indexes) - used_question_indexes)

            if (count > len(indexes)):
                logging.warning("Group '%s' does not have enough questions to pick without replacement, now choosing questions with replacement.", self.name)
                # Reset the selection pool.
                indexes = list(range(len(self.children)))
                used_question_indexes.clear()

        rng.shuffle(indexes)
        indexes = indexes[:count]

        if (not with_replacement):
            used_question_indexes |= set(indexes)

        questions = []
        for index in indexes:
            question = self.children[index].copy()
            question.shuffle(rng)

            questions.append(question)

        return questions
