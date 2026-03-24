import dataclasses
import enum
import os
import string
import typing

import edq.util.parse
import edq.util.serial

import quizcomp.errors
import quizcomp.model.answer
import quizcomp.model.base
import quizcomp.model.feedback
import quizcomp.model.text
import quizcomp.parser.public

DEFAULT_PROMPT_FILENAME: str = 'prompt.md'

MAX_CHOICES: int = len(string.ascii_uppercase)

class QuestionType(enum.StrEnum):
    """ The types of questions supported by the Quiz Composer. """

    ESSAY = 'essay'
    FIMB = 'fill_in_multiple_blanks'
    FITB = 'fill_in_the_blank'
    MATCHING = 'matching'
    MA = 'multiple_answers'
    MCQ = 'multiple_choice'
    MDD = 'multiple_dropdowns'
    NUMERICAL = 'numerical'
    SA = 'short_answer'
    TEXT_ONLY = 'text_only'
    TF = 'true_false'

@dataclasses.dataclass
class QuestionOptions(edq.util.serial.DictConverter):
    """ Standard options that can appear with a group or question. """

    def __init__(self,
            name: str = '',
            points: float = 0,
            shuffle_answers: bool = True,
            skip_numbering: bool = False,
            custom_header: typing.Union[str, None] = None,
            feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = None,
            **kwargs: typing.Any) -> None:
        self.name: str = name
        """ The name. """

        self.points: float = points
        """ The number of points possible. """

        self.shuffle_answers: bool = shuffle_answers
        """ Whether the answers should be shuffled. """

        self.skip_numbering: typing.Union[bool, None] = skip_numbering
        """ Whether to skip numbering. """

        self.custom_header: typing.Union[str, None] = custom_header
        """ A custom header, instead of something generic like "Question 4". """

        self.feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = feedback
        """ Object-level feedback. """

class Question(quizcomp.model.base.CoreType):
    """ A class that represents a question and all answers/feedback for the question. """

    def __init__(self,
            question_type: quizcomp.model.question.QuestionType,
            prompt: quizcomp.model.text.ParsedText,
            answers: quizcomp.model.answer.QuestionAnswers,
            options: typing.Union[QuestionOptions, None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        self.question_type: quizcomp.model.question.QuestionType = question_type
        """ The type of this question. """

        self.prompt: quizcomp.model.text.ParsedText = prompt
        """ The parsed prompt of this question. """

        self.answers: quizcomp.model.answer.QuestionAnswers = answers
        """ The answers for this question. """

        if (options is None):
            options = QuestionOptions()

        self.options: QuestionOptions = options
        """ Options for this question. """

    def to_dict(self, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
        data = super().to_dict()

        data['question_type'] = self.question_type.value
        data['prompt'] = self.prompt.text

        # Instead of putting these values as nested dicts, add their keys directly.
        data.update(self.options.to_dict())
        data.update(self.answers.to_dict())

        return data

    @classmethod
    def prep_init_data(cls,
            data: typing.Dict[str, typing.Any],
            base_dir: typing.Union[str, None] = None,
            **kwargs: typing.Any,
            ) -> typing.Dict[str, typing.Any]:
        data = super().prep_init_data(data)

        data['options'] = QuestionOptions.from_dict(data)
        data['answers'] = _answers_from_dict(data.get('question_type', None), data.get('answers', None), base_dir)
        data['prompt'] = cls._collect_prompt(data.get('prompt', None), data.get('prompt_path', None), base_dir)

        return data

    @classmethod
    def _collect_prompt(cls,
            text: typing.Union[str, None] = '',
            path: typing.Union[str, None] = None,
            base_dir: typing.Union[str, None] = None,
            ) -> quizcomp.model.text.ParsedText:
        """
        Collect the prompt from one of several possible locations.

        The prompt is allowed to appear (in order of priority):
        1) in the `prompt` field (`text` argument),
        2) pointed to by the `prompt_path` field (`path` argument),
        3) or be in `<base dir>/DEFAULT_PROMPT_FILENAME`.

        Will raise an exception on an empty prompt.
        Null, empty, and only white strings all count as empty.
        """

        if (text is None):
            text = ''

        if (base_dir is None):
            base_dir = '.'

        text = text.strip()
        if (len(text) != 0):
            return quizcomp.parser.public.parse_text(text, base_dir = base_dir)

        if (path is not None):
            return quizcomp.parser.public.parse_file(path, base_dir = base_dir)

        path = os.path.abspath(os.path.join(base_dir, DEFAULT_PROMPT_FILENAME))
        if (not os.path.isfile(path)):
            raise quizcomp.errors.QuestionValidationError("Could not find any non-empty prompt.")

        return quizcomp.parser.public.parse_file(path, base_dir = base_dir)

def _answers_from_dict(
        raw_question_type: typing.Union[QuestionType, str, None],
        raw_data: typing.Union[typing.Any, None],
        base_dir: typing.Union[str, None] = None,
        ) -> quizcomp.model.answer.QuestionAnswers:
    """
    Create an answers object for a specific question type from some serialized data
    This data will normally come from a JSON file.
    Because of the differing nature of questions, several different forms of answers may need to be processed
    (even for the same question type).
    """

    if (raw_question_type is None):
        raise quizcomp.errors.QuestionValidationError("Could not parse question answers because of lack of question type.")

    question_type = QuestionType(raw_question_type)

    if (question_type == QuestionType.MCQ):
        return _answers_from_dict_mcq(raw_data, base_dir)
    else:
        raise quizcomp.errors.QuestionValidationError(f"Unknown question type: '{raw_question_type}'.")

def _answers_from_dict_mcq(
        raw_data: typing.Union[typing.Any, None],
        base_dir: typing.Union[str, None] = None,
        ) -> quizcomp.model.answer.QuestionAnswers:
    """ Create answers for an MCQ. """

    choices = _parse_choices(raw_data, min_correct = 1, base_dir = base_dir)
    return quizcomp.model.answer.ChoiceAnswers(choices)

def _parse_choices(
        raw_data: typing.Union[typing.Any, None],
        min_correct: int = 0,
        max_correct: int = MAX_CHOICES,
        base_dir: typing.Union[str, None] = None,
        ) -> typing.List[quizcomp.model.text.ParsedTextChoice]:
    """ Check that the given answers are a list with the specified range of correct choices. """

    quizcomp.errors.check_type(raw_data, list, "'answers'")

    raw_choices: typing.List[typing.Any] = typing.cast(list, raw_data)

    if (len(raw_choices) == 0):
        raise quizcomp.errors.QuestionValidationError("No answers provided, at least one answer required.", base_dir = base_dir)

    num_correct = 0
    choices = []

    for (i, raw_choice) in enumerate(raw_choices):
        # TEST - Check that choice is a dict.
        label = f"Choice at index {i}"

        raw_correct = raw_choice.get('correct', None)
        if (raw_correct is None):
            raise quizcomp.errors.QuestionValidationError(f"{label} has no 'correct' field set.", base_dir = base_dir)

        raw_text = raw_choice.get('text', None)
        if (raw_text is None):
            raise quizcomp.errors.QuestionValidationError(f"{label} has no 'text' field set.", base_dir = base_dir)

        correct = edq.util.parse.soft_boolean(raw_correct)
        if (correct is None):
            raise quizcomp.errors.QuestionValidationError(f"{label}'s 'correct' field does not contain a boolean: '{raw_correct}'.")

        if (correct):
            num_correct += 1

        parsed_text = quizcomp.parser.public.parse_text(raw_text, base_dir = base_dir)
        feedback = quizcomp.model.feedback.Feedback.from_dict(raw_choice)

        choices.append(quizcomp.model.answer.Choice(parsed_text, correct, feedback))

    if (num_correct < min_correct):
        raise quizcomp.errors.QuestionValidationError(("Did not find enough correct choices."
            + f" Expected at least {min_correct}, found {num_correct}."),
            base_dir = base_dir)

    if (num_correct > max_correct):
        raise quizcomp.errors.QuestionValidationError(("Found too many correct choices."
            + f" Expected at most {max_correct}, found {num_correct}."),
            base_dir = base_dir)

    return choices
