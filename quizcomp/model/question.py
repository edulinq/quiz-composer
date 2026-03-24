import dataclasses
import enum
import os
import typing

import edq.util.parse
import edq.util.serial

import quizcomp.errors
import quizcomp.model.answer
import quizcomp.model.base
import quizcomp.model.feedback
import quizcomp.parser.document

DEFAULT_PROMPT_FILENAME: str = 'prompt.md'

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
            question_type: quizcomp.model.constants.QuestionType,
            prompt: quizcomp.parser.document.ParsedDocument,
            answers: quizcomp.model.answer.QuestionAnswers,
            options: typing.Union[QuestionOptions, None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        self.question_type: quizcomp.model.constants.QuestionType = question_type
        """ The type of this question. """

        self.prompt: quizcomp.parser.document.ParsedDocument = prompt
        """ The parsed prompt of this question. """

        self.answers: quizcomp.model.answer.QuestionAnswers = answers
        """ The answers for this question. """

        if (options is None):
            options = QuestionOptions()

        self.options: QuestionOptions = options
        """ Options for this question. """

    def to_dict(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> typing.Dict[str, typing.Any]:
        data = super().to_dict()

        data['question_type'] = self.question_type.value
        data['prompt'] = self.prompt.text

        # Instead of putting these values as nested dicts, add their keys directly.
        data.pop('options', None)
        data.update(self.options.to_dict())

        return data

    @classmethod
    def prep_init_data(cls,
            data: typing.Dict[str, typing.Any],
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> typing.Dict[str, typing.Any]:
        if (serialization_options is None):
            serialization_options = {}

        serialization_options['question_type'] = data.get('question_type', None)

        data = super().prep_init_data(data, serialization_options)

        base_dir = serialization_options.get('base_dir', None)

        data['options'] = QuestionOptions.from_dict(data)
        data['prompt'] = cls._collect_prompt(data.get('prompt', None), data.get('prompt_path', None), base_dir)

        return data

    @classmethod
    def _collect_prompt(cls,
            text: typing.Union[quizcomp.parser.document.ParsedDocument:, str, None] = None,
            path: typing.Union[str, None] = None,
            base_dir: typing.Union[str, None] = None,
            ) -> quizcomp.parser.document.ParsedDocument:
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

        if (isinstance(text, quizcomp.parser.document.ParsedDocument)):
            return text

        text = text.strip()
        if (len(text) != 0):
            return quizcomp.parser.document.ParsedDocument.parse_text(text, base_dir = base_dir)

        if (path is not None):
            return quizcomp.parser.document.ParsedDocument.parse_file(path, base_dir = base_dir)

        path = os.path.abspath(os.path.join(base_dir, DEFAULT_PROMPT_FILENAME))
        if (not os.path.isfile(path)):
            raise quizcomp.errors.QuestionValidationError("Could not find any non-empty prompt.")

        return quizcomp.parser.document.ParsedDocument.parse_file(path, base_dir = base_dir)
