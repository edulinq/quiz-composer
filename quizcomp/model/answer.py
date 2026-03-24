import string
import typing

import edq.util.serial

import quizcomp.errors
import quizcomp.model.feedback

MAX_CHOICES: int = len(string.ascii_uppercase)

class Choice(edq.util.serial.DictConverter):
    """
    One possible choice for an answer.
    This is for questions with a finite number of choices (e.g., MCQ, MA, TF).
    """

    _dictconverter_options = edq.util.serial.DictConverterOptions(
        omit_none = True,
    )

    def __init__(self,
            text: quizcomp.parser.document.ParsedDocument,
            correct: bool,
            feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = None,
            **kwargs: typing.Any) -> None:
        self.text: quizcomp.parser.document.ParsedDocument = text
        """ The text/label for this choice. """

        self.correct: bool = correct
        """ Whether this choice is a correct answer. """

        if ((feedback is not None) and feedback.is_empty()):
            feedback = None

        self.feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = feedback
        """ Feedback specific to this choice. """

class QuestionAnswers(edq.util.serial.PODConverter):
    """
    The base type that represents all the listed answers/choices for a question.
    The exact contents of answers vary depending on the question's type.
    """

    def __init__(self, **kwargs: typing.Any) -> None:
        pass

    @classmethod
    def from_pod(cls: typing.Type[QuestionAnswers],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> QuestionAnswers:
        """
        Create an answers object for a specific question type from some serialized data
        This data will normally come from a JSON file.
        Because of the differing nature of questions, several different forms of answers may need to be processed
        (even for the same question type).

        This function will not return a generic QuestionAnswers, but a subclass of QuestionAnswers.
        """

        if (serialization_options is None):
            serialization_options = {}

        raw_question_type = serialization_options.get('question_type', None)
        base_dir = serialization_options.get('base_dir', None)

        if (raw_question_type is None):
            raise quizcomp.errors.QuestionValidationError("Could not parse question answers because of lack of question type.")

        question_type = quizcomp.model.constants.QuestionType(raw_question_type)

        if (question_type == quizcomp.model.constants.QuestionType.MCQ):
            return _answers_from_dict_mcq(data, base_dir)
        else:
            raise quizcomp.errors.QuestionValidationError(f"Unknown question type: '{raw_question_type}'.")

class ChoiceAnswers(QuestionAnswers):
    """ Answers that include a finite set of choices. """

    def __init__(self,
            choices: typing.List[Choice],
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        self.choices: typing.List[Choice] = choices
        """ The possible choices. """

    # TEST - This should be in edq (handling a list (or dict)).
    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return [choice.to_dict() for choice in self.choices]

def _answers_from_dict_mcq(
        raw_data: typing.Union[typing.Any, None],
        base_dir: typing.Union[str, None] = None,
        ) -> ChoiceAnswers:
    """ Create answers for an MCQ. """

    choices = _parse_choices(raw_data, min_correct = 1, base_dir = base_dir)
    return ChoiceAnswers(choices)

def _parse_choices(
        raw_data: typing.Union[typing.Any, None],
        min_correct: int = 0,
        max_correct: int = MAX_CHOICES,
        base_dir: typing.Union[str, None] = None,
        ) -> typing.List[Choice]:
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

        parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(raw_text, base_dir = base_dir)
        feedback = quizcomp.model.feedback.Feedback.from_raw_data(raw_choice.get('feedback', None), base_dir = base_dir)

        choices.append(Choice(parsed_text, correct, feedback))

    if (num_correct < min_correct):
        raise quizcomp.errors.QuestionValidationError(("Did not find enough correct choices."
            + f" Expected at least {min_correct}, found {num_correct}."),
            base_dir = base_dir)

    if (num_correct > max_correct):
        raise quizcomp.errors.QuestionValidationError(("Found too many correct choices."
            + f" Expected at most {max_correct}, found {num_correct}."),
            base_dir = base_dir)

    return choices

# TEST
''' TEST
    def _validate_self_answer_list(self, min_correct: int = 0, max_correct: int = MAX_CHOICES) -> None:
        """ Check that the answers are a list with the specified range of correct choices. """

        self.answers = self._validate_answer_list(self.answers, self.base_dir,
                min_correct = min_correct, max_correct = max_correct)

    def _validate_answer_list(self,
            answers: typing.List[typing.Dict[str, typing.Any]],
            base_dir: str,
            min_correct: int = 0,
            max_correct: int = MAX_CHOICES,
            ) -> typing.List[quizcomp.model.text.ParsedTextChoice]:
        """ Check that the given answers are a list with the specified range of correct choices. """

        self._check_type(answers, list, "'answers'")

        if (len(answers) == 0):
            raise quizcomp.common.QuestionValidationError("No answers provided, at least one answer required.", ids = self.ids)

        num_correct = 0
        for answer in answers:
            if ('correct' not in answer):
                raise quizcomp.common.QuestionValidationError("Answer has no 'correct' field.", ids = self.ids)

            if ('text' not in answer):
                raise quizcomp.common.QuestionValidationError("Answer has no 'text' field.", ids = self.ids)

            if (answer['correct']):
                num_correct += 1

        if (num_correct < min_correct):
            raise quizcomp.common.QuestionValidationError(("Did not find enough correct answers."
                + f" Expected at least {min_correct}, found {num_correct}."),
                ids = self.ids)

        if (num_correct > max_correct):
            raise quizcomp.common.QuestionValidationError(("Found too many correct answers."
                + f" Expected at most {max_correct}, found {num_correct}."),
                ids = self.ids)

        new_answers = []
        for (i, answer) in enumerate(answers):
            parsed_text = self._validate_text_item(answer, f"'answers' values (element {i})")
            new_answer = quizcomp.model.text.ParsedTextChoice(parsed_text, answer['correct'])
            new_answers.append(new_answer)

        return new_answers

    def _validate_text_answers(self) -> None:
        """ Check that the answers are valid text answer. """

        possible_answers = 'null/None, string, empty list, list of strings, or list of objects'

        if (self.answers is None):
            self.answers = ['']
        elif (isinstance(self.answers, str)):
            self.answers = [self.answers]

        if (not isinstance(self.answers, list)):
            raise quizcomp.common.QuestionValidationError(
                    f"'answers' value must be {possible_answers}, found: {self.answers}.", ids = self.ids)

        if (len(self.answers) == 0):
            self.answers = ['']

        new_answers = []
        for (i, answer) in enumerate(self.answers):
            new_answers.append(self._validate_text_item(answer, f"'answers' values (element {i})"))

        self.answers = new_answers

    def _validate_text_item(self,
            item: typing.Union[str, typing.Dict[str, typing.Any], quizcomp.model.text.ParsedTextWithFeedback],
            label: str,
            check_feedback: bool = True,
            allow_empty: bool = True,
            strip: bool = True,
            clean_whitespace: bool = False,
            ) -> quizcomp.model.text.ParsedTextWithFeedback:
        """
        Validate a portion of an answer/choice/field that is a parsed string.

        Allowed values are:
         - None (will be converted to an empty string).
         - Empty String (if allow_empty is True).
         - String
         - quizcomp.model.text.ParsedTextWithFeedback (will be passed back without any checks).
         - Dict with required key 'text' and optional key 'feedback'.

        If no exception is raised, a quizcomp.model.text.ParsedTextWithFeedback (child of quizcomp.parser.document.ParsedDocument)
        will be returned, even if there is no feedback.
        """

        if (isinstance(item, quizcomp.model.text.ParsedTextWithFeedback)):
            # Nothing to do if the item is already parsed.
            return item

        if (item is None):
            item = ''

        if (isinstance(item, str)):
            item = {'text': item}

        self._check_type(item, dict, label)

        if ('text' not in item):
            raise quizcomp.common.QuestionValidationError(f"{label} is missing a 'text' key.", ids = self.ids)

        text = item['text']
        self._check_type(item['text'], str, f"{label} 'text' key")

        if (clean_whitespace):
            text = re.sub(r'\s+', ' ', text)

        if (strip):
            text = text.strip()

        if ((not allow_empty) and (text == '')):
            raise quizcomp.common.QuestionValidationError(f"{label} text is empty.", ids = self.ids)

        feedback = None
        if (check_feedback):
            feedback = self._validate_feedback_item(item.get('feedback', None), label)

        return quizcomp.model.text.ParsedTextWithFeedback(quizcomp.parser.public.parse_text(text,
                base_dir = self.base_dir), feedback = feedback)

    def _validate_fimb_answers(self) -> None:
        """ Check that the answers are valid fill in multiple blanks answers. """

        self._check_type(self.answers, dict, "'answers' key")

        if (len(self.answers) == 0):
            raise quizcomp.common.QuestionValidationError("Expected 'answers' dict to be non-empty.", ids = self.ids)

        for (key, values) in self.answers.items():
            # If this was already in the full FIMB format, then we need to pull out the values.
            if ((isinstance(values, dict)) and ('values' in values)):
                self.answers[key] = values['values']
            elif (not isinstance(values, list)):
                self.answers[key] = [values]

        new_answers = {}

        for (key, values) in self.answers.items():
            self._check_type(key, str, "key in 'answers' dict")

            if (len(values) == 0):
                raise quizcomp.common.QuestionValidationError("Expected possible values to be non-empty.", ids = self.ids)

            new_values = []
            for (i, value) in enumerate(values):
                label = f"answers key '{key}' index {i}"
                new_values.append(self._validate_text_item(value, label))

            new_answers[key] = {
                'key': quizcomp.parser.public.parse_text(key, base_dir = self.base_dir),
                'values': new_values,
            }

        self.answers = new_answers

        self._check_placeholders(self.answers.keys())

    def _check_type(self, value: typing.Any, expected_type: typing.Type, label: str) -> None:
        """ Check that the given value has the expected type. """

        if (not isinstance(value, expected_type)):
            raise quizcomp.common.QuestionValidationError(f"{label} must be a {expected_type}, found '{value}' ({type(value)}).",
                    ids = self.ids)

    def _check_placeholders(self, answer_placeholders: typing.Set[str]) -> None:
        """
        Check placeholders from the answers against placeholders in the prompt.
        """

        document_placeholders = self.prompt.document.collect_placeholders()

        # Special case for FITB documents.
        if ((len(answer_placeholders) == 1) and (list(answer_placeholders)[0] == '')):
            if (len(document_placeholders) != 0):
                output_answer_placeholders = list(sorted(answer_placeholders))
                raise quizcomp.common.QuestionValidationError(
                        f"Found placeholders ({output_answer_placeholders}) in the question prompt when none were expected.",
                        ids = self.ids)

            return

        if (answer_placeholders != document_placeholders):
            output_answer_placeholders = list(sorted(answer_placeholders))
            output_document_placeholders = list(sorted(document_placeholders))

            raise quizcomp.common.QuestionValidationError(
                    (f"Mismatch between the placeholders found in the question prompt ({output_document_placeholders})"
                        + f" and answers config ({output_answer_placeholders})."),
                    ids = self.ids)
'''

# TEST
''' TEST
class NumericChoice(edq.util.serial.DictConverter):
    """
    Numeric choices have no parsed text (aside from optional feedback).
    """

    def __init__(self,
            type: str,
            margin: typing.Union[float, None] = None,
            min: typing.Union[float, None] = None,
            max: typing.Union[float, None] = None,
            value: typing.Union[float, None] = None,
            precision: typing.Union[int, None] = None,
            feedback: typing.Union[ParsedText, None] = None,
            ) -> None:
        self.type: str = type
        """ The type of numeric answer for this choice. """

        self.margin: typing.Union[float, None] = margin
        """ The allowed/error margin. """

        self.min: typing.Union[float, None] = min
        """ The min value. """

        self.max: typing.Union[float, None] = max
        """ The max value. """

        self.value: typing.Union[float, None] = value
        """ The expected/correct value. """

        self.precision: typing.Union[int, None] = precision
        """ The number of expected significant places. """

        self.feedback: typing.Union[ParsedText, None] = feedback
        """ Feedback associated with this text. """
'''
