import glob
import logging
import math
import os
import random
import typing

import edq.util.serial

import quizcomp.model.base
import quizcomp.model.config
import quizcomp.model.constants
import quizcomp.model.errors
import quizcomp.model.question

_logger = logging.getLogger(__name__)

DEFAULT_PICK_COUNT: int = 1
""" The default number of questions chosen from this group. """

class Group(quizcomp.model.base.CoreType):
    """
    A group/bank of questions for a quiz.
    Questions can be grouped together and then a subset can be randomly chosen to create variety in quizzes.
    """

    def __init__(self,
            children: typing.Union[typing.List[quizcomp.model.question.Question], None] = None,
            pick_count: int = DEFAULT_PICK_COUNT,
            **kwargs: typing.Any) -> None:
        # Remove aliases before super construction.
        kwargs.pop('questions', None)

        super().__init__(children = children, **kwargs)

        if (pick_count < 0):
            raise quizcomp.model.errors.QuizValidationError(f"Pick count must be non-negative, found: {pick_count}.", context = self)

        self.pick_count: int = pick_count
        """ The number of questions to choose from this group. """

        if (self.pick_count > self.child_count()):
            _logger.warning("Group '%s' was asked to pick more questions than available (pick count: %d, group size: %d).",
                    self.name, self.pick_count, self.child_count())
            self.pick_count = self.child_count()

    def get_questions(self) -> typing.List[quizcomp.model.question.Question]:
        """ Get all questions for this group. """

        return [typing.cast(quizcomp.model.question.Question, child) for child in self.children]

    def get_child_points(self) -> typing.Union[float, int]:
        if (self.pick_count == 0):
            return 0

        # Make sure to not try to use the children to compute the available points.
        value = self.get_points(check_children = False) / float(self.pick_count)
        if (math.isclose(value, int(value))):
            value = int(value)

        return value

    def choose_variant_questions(self,
            all_questions: bool,
            used_question_indexes: typing.Set[int],
            rng: random.Random,
            ) -> typing.List[quizcomp.model.question.Question]:
        """
        Get a list of questions to use for an instantiated variant of this group.
        The returned questions will be copies of the original and shuffled (if set in config).
        """

        if ((self.pick_count == 0) or (self.child_count() == 0)):
            _logger.warning("Group '%s' will select no questions (pick_count: %d, group size: %d).",
                    self.name, self.pick_count, self.child_count())
            return []

        count = self.pick_count
        if (all_questions):
            count = self.child_count()

        questions = self._choose_questions(count, used_question_indexes, rng)

        return questions

    def _choose_questions(self,
            count: int,
            used_question_indexes: typing.Set[int],
            rng: random.Random,
            ) -> typing.List[quizcomp.model.question.Question]:
        """ Internally, choose a list of questions to use for an instantiated variant of this group. """

        indexes = list(range(self.child_count()))

        with_replacement = (self.get_config(quizcomp.model.config.OPTION_PICK_WITH_REPLACEMENT) is True)

        if (not with_replacement):
            indexes = list(set(indexes) - used_question_indexes)

            if (count > len(indexes)):
                _logger.warning(
                    "Group '%s' does not have enough questions to pick without replacement, now choosing questions with replacement.",
                    self.name,
                )
                # Reset the selection pool.
                indexes = list(range(self.child_count()))
                used_question_indexes.clear()

        rng.shuffle(indexes)
        indexes = indexes[:count]

        if (not with_replacement):
            used_question_indexes |= set(indexes)

        questions = []
        for index in indexes:
            question = typing.cast(quizcomp.model.question.Question, self.children[index].copy())
            question.shuffle(rng)

            questions.append(question)

        return questions

    def to_dict(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> typing.Dict[str, edq.util.serial.PODType]:
        data = super().to_dict(context)
        data['questions'] = data.pop('children', data.get('questions', None))
        return data

    @classmethod
    def from_dict(cls,
            data: typing.Dict[str, edq.util.serial.PODType],
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> 'Group':
        if (context is None):
            context = edq.util.serial.SerializationContext()

        # Expand any question paths that be directories.
        cls._expand_questions(data, context)
        return super().from_dict(data, context)

    @classmethod
    def _expand_questions(cls,
            data: typing.Dict[str, edq.util.serial.PODType],
            context: edq.util.serial.SerializationContext,
            ) -> None:
        """
        Expand the 'questions' field into the 'children' field,
        in a form that Question.from_pod() can read
        (which includes a path to a question).

        This allows questions to be provided as a path.
        If that path is a dir, then recursivley load all questions found in that dir.
        """

        new_questions: typing.List[edq.util.serial.PODType] = []
        raw_questions = data.pop('questions', data.get('children', []))

        quizcomp.model.errors.check_type(raw_questions, list, "'questions'", context = context)
        old_questions = typing.cast(typing.List[edq.util.serial.PODType], raw_questions)

        for raw_question in old_questions:
            if (not isinstance(raw_question, str)):
                new_questions.append(raw_question)
                continue

            path = str(raw_question)
            if (not os.path.isabs(path)):
                path = os.path.join(context.base_dir, path)

            path = os.path.abspath(path)

            if (os.path.isdir(path)):
                for subpath in sorted(glob.glob(os.path.join(path, '**', quizcomp.model.constants.QUESTION_FILENAME), recursive = True)):
                    new_questions.append(subpath)

            else:
                new_questions.append(path)

        data['children'] = new_questions
