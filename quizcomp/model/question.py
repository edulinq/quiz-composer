import dataclasses
import os
import random
import typing

import edq.util.enum
import edq.util.parse
import edq.util.serial

import quizcomp.errors
import quizcomp.model.answer
import quizcomp.model.base
import quizcomp.model.config
import quizcomp.model.constants
import quizcomp.model.feedback
import quizcomp.parser.document

DEFAULT_PROMPT_FILENAME: str = 'prompt.md'

EMPTY_ANSWER_QUESTION_TYPES: typing.Set[quizcomp.model.constants.QuestionType] = {
    quizcomp.model.constants.QuestionType.ESSAY,
    quizcomp.model.constants.QuestionType.SA,
    quizcomp.model.constants.QuestionType.TEXT_ONLY,
}
""" Question types that do not have to have an answer. """

PLACEHOLDER_QUESTION_TYPES: typing.Set[quizcomp.model.constants.QuestionType] = {
    quizcomp.model.constants.QuestionType.FIMB,
    quizcomp.model.constants.QuestionType.MDD,
}
""" Question types that have placeholders. """

class Question(quizcomp.model.base.CoreType):
    """ A class that represents a question and all answers/feedback for the question. """

    def __init__(self,
            question_type: quizcomp.model.constants.QuestionType,
            prompt: quizcomp.parser.document.ParsedDocument,
            answers: typing.Union[quizcomp.model.answer.QuestionAnswers, None] = None,
            feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        self.question_type: quizcomp.model.constants.QuestionType = question_type
        """ The type of this question. """

        self.prompt: quizcomp.parser.document.ParsedDocument = prompt
        """ The parsed prompt of this question. """

        if (answers is None):
            answers = quizcomp.model.answer.TextAnswers()

        self.answers: quizcomp.model.answer.QuestionAnswers = answers
        """ The answers for this question. """

        self.feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = feedback
        """ Object-level feedback. """

    @classmethod
    def from_pod(cls,
            data: edq.util.serial.PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> 'Question':
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', '.')

        if (isinstance(data, dict)):
            return super().from_pod(data, serialization_options)

        if (not isinstance(data, str)):
            raise quizcomp.errors.QuizValidationError(f"Cannot createquestion object from '{type(data)}' type, need dict or str (path).")

        # If a question is being loaded from a string, it is probably a path.
        path = str(data)
        if (not os.path.isabs(path)):
            path = os.path.join(base_dir, path)

        path = os.path.abspath(path)

        return cls.from_path(path, serialization_options)

    @classmethod
    def prep_init_data(cls,
            data: typing.Dict[str, typing.Any],
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> typing.Dict[str, typing.Any]:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        raw_question_type = data.get('question_type', None)
        if (raw_question_type is None):
            raise quizcomp.errors.QuestionValidationError("Question data does not include 'question_type'.", base_dir = base_dir)

        question_type = quizcomp.model.constants.QuestionType(raw_question_type)
        serialization_options['question_type'] = question_type

        raw_feedback = data.pop('feedback', None)

        data = super().prep_init_data(data, serialization_options)

        data['prompt'] = cls._collect_prompt(data.get('prompt', None), data.get('prompt_path', None), base_dir)
        data['feedback'] = quizcomp.model.feedback.Feedback.from_raw_data(raw_feedback, base_dir = base_dir)

        cls._validate_init_data(data, serialization_options)

        return data

    @classmethod
    def _validate_init_data(cls, data: typing.Dict[str, typing.Any], serialization_options: typing.Dict[str, typing.Any]) -> None:
        """ Validate the data to be sent to __init__() right before construction. """

        base_dir = serialization_options.get('base_dir', None)

        question_type = data.get('question_type', None)
        if (not edq.util.enum.has_value(quizcomp.model.constants.QuestionType, question_type)):
            raise quizcomp.errors.QuestionValidationError(f"Unknown question type: '{question_type}'.", base_dir = base_dir)

        answers = data.get('answers', None)
        if (answers is None):
            if (question_type not in EMPTY_ANSWER_QUESTION_TYPES):
                raise quizcomp.errors.QuestionValidationError('No answers to question provided.', base_dir = base_dir)

            data['answers'] = quizcomp.model.answer.TextAnswers()

        prompt_placeholders = data['prompt'].collect_placeholders()
        if (question_type in PLACEHOLDER_QUESTION_TYPES):
            answers_placeholders = set(data['answers'].parts.keys())

            if (answers_placeholders != prompt_placeholders):
                output_answers_placeholders = list(sorted(answers_placeholders))
                output_prompt_placeholders = list(sorted(prompt_placeholders))

                raise quizcomp.errors.QuestionValidationError(
                        (f"Mismatch between the placeholders found in the question prompt ({output_prompt_placeholders})"
                            + f" and answers config ({output_answers_placeholders})."),
                        base_dir = base_dir)
        elif (len(prompt_placeholders) != 0):
            raise quizcomp.errors.QuestionValidationError(
                    f"Found placeholders in the prompt for questions that do not use placeholders: '{question_type}'.",
                    base_dir = base_dir)

    @classmethod
    def _collect_prompt(cls,
            text: typing.Union[quizcomp.parser.document.ParsedDocument:, str, None] = None,
            path: typing.Union[str, None] = None,
            base_dir: typing.Union[str, None] = None,
            ) -> quizcomp.parser.document.ParsedDocument:
        """
        Collect the prompt from one of several possible locations.

        The prompt is allowed to appear (in order of priority):
        1) in the `prompt` field (sent to this function as the `text` argument),
        2) pointed to by the `prompt_path` field (send to this function as the `path` argument),
        3) or be in `<base dir>/DEFAULT_PROMPT_FILENAME`.

        Will raise an exception on an empty prompt.
        Null, empty, and only white space all count as empty.
        """

        if (text is None):
            text = ''

        if (base_dir is None):
            base_dir = '.'

        if (isinstance(text, quizcomp.parser.document.ParsedDocument)):
            return text

        text = text.strip()
        if (len(text) != 0):
            return quizcomp.parser.document.ParsedDocument.parse_text(text, base_dir = base_dir)

        if (path is not None):
            return quizcomp.parser.document.ParsedDocument.parse_file(path, base_dir = base_dir)

        path = os.path.abspath(os.path.join(base_dir, DEFAULT_PROMPT_FILENAME))
        if (not os.path.isfile(path)):
            raise quizcomp.errors.QuestionValidationError("Could not find any non-empty prompt.", base_dir = base_dir)

        return quizcomp.parser.document.ParsedDocument.parse_file(path, base_dir = base_dir)

    def shuffle(self, rng: random.Random) -> None:
        """
        Shuffle the answers for this question.
        This method will do nothing if question shuffling is not allowed by the config settings.
        """

        if (self.get_config(quizcomp.model.config.OPTION_SHUFFLE_ANSWERS) is not True):
            return

        self.answers.shuffle(rng)
