import glob
import logging
import os
import random
import typing

import edq.util.serial

import quizcomp.common
import quizcomp.constants
import quizcomp.model.base
import quizcomp.model.config
import quizcomp.question.base
import quizcomp.util.serial

DEFAULT_PICK_COUNT: int = 1
""" The default number of questions chosen from this group. """

# TEST - Make some tests.

class Group(quizcomp.model.base.CoreType):
    """
    A group/bank of questions for a quiz.
    Questions can be grouped together and then a subset can be randomly chosen to create variety in quizzes.
    """

    def __init__(self,
            children: typing.Union[typing.List[quizcomp.model.question.Question], None] = None,
            pick_count: int = DEFAULT_PICK_COUNT,
            **kwargs: typing.Any) -> None:
        super().__init__(children = children, **kwargs)

        if (pick_count < 0):
            raise quizcomp.common.QuizValidationError(f"Pick count must be non-negative, found: {pick_count}.", base_dir = base_dir)

        self.pick_count: int = pick_count
        """ The number of questions to choose from this group. """

        if (self.pick_count > len(self.children)):
            logging.warning("Group '%s' was asked to pick more questions than available (pick count: %d, group size: %d).",
                    self.name, self.pick_count, len(self.children))
            self.pick_count = len(self.children)

    def choose_variant_questions(self,
            all_questions: bool,
            used_question_indexes: typing.Set[int],
            rng: random.Random,
            ) -> typing.List[quizcomp.question.base.Question]:
        """
        Get a list of questions to use for an instantiated variant of this group.
        The returned questions will be copies of the original and shuffled (if set in config).
        """

        if ((self.pick_count == 0) or (len(self.children) == 0)):
            logging.warning("Group '%s' will select no questions (pick_count: %d, group size: %d).",
                    self.name, self.pick_count, len(self.children))
            return []

        count = self.pick_count
        if (all_questions):
            count = len(self.children)

        questions = self._choose_questions(count, used_question_indexes, rng)

        # Rename questions if there are more than one.
        if (len(questions) > 1):
            for (i, question) in enumerate(questions):
                question.name = f"{self.name} - {i + 1}"

        return questions

    def _choose_questions(self,
            count: int,
            used_question_indexes: typing.Set[int],
            rng: random.Random,
            ) -> typing.List[quizcomp.question.base.Question]:
        """ Internally, choose a list of questions to use for an instantiated variant of this group. """

        indexes = list(range(len(self.children)))

        with_replacement = (self.get_config(quizcomp.model.config.OPTION_PICK_WITH_REPLACEMENT) is True)

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

    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        data = super().to_pod(serialization_options)
        data['questions'] = data.pop('children', data.get('questions', None))
        return data

    @classmethod
    def from_pod(cls,
            data: edq.util.serial.PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> 'Group':
        # Expand any question paths that be directories.
        cls._expand_questions(data, serialization_options)
        return super().from_pod(data, serialization_options)

    @classmethod
    def _expand_questions(cls,
            data: typing.Dict[str, edq.util.serial.PODType],
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> None:
        """
        Expand the 'questions' field.
        This allows questions to be provided as a path.
        If that path is a dir, then recursivley load all questions found in that dir.
        """

        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', '.')

        new_questions = []
        raw_questions = data.pop('questions', data.get('children', []))

        for raw_question in raw_questions:
            if (not isinstance(raw_question, str)):
                new_questions.append(raw_question)
                continue

            path = str(raw_question)
            if (not os.path.isabs(path)):
                path = os.path.join(base_dir, path)

            path = os.path.abspath(path)

            if (os.path.isdir(path)):
                for subpath in sorted(glob.glob(os.path.join(path, '**', quizcomp.constants.QUESTION_FILENAME), recursive = True)):
                    new_questions.append(subpath)

            else:
                new_questions.append(path)

        data['children'] = new_questions
