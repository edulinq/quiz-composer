import typing

import edq.util.serial

import quizcomp.errors
import quizcomp.model.text
import quizcomp.parser.public

class Feedback(edq.util.serial.DictConverter):
    """
    Text that can be attached to objects (generally questions and answers) as a form of feedback for an action.
    Feedback can be specific to a correct/incorrect action, or just general.
    """

    # TEST - These should all be ParsedText
    def __init__(self,
            general: typing.Union[quizcomp.model.text.ParsedText, None] = None,
            correct: typing.Union[quizcomp.model.text.ParsedText, None] = None,
            incorrect: typing.Union[quizcomp.model.text.ParsedText, None] = None,
            **kwargs: typing.Any) -> None:
        self.general: typing.Union[quizcomp.model.text.ParsedText, None] = general
        """ Feedback to be shown regardless of the outcome. """

        self.correct: typing.Union[quizcomp.model.text.ParsedText, None] = correct
        """ Feedback to be shown if the action/choice/answer was correct. """

        self.incorrect: typing.Union[quizcomp.model.text.ParsedText, None] = incorrect
        """ Feedback to be shown if the action/choice/answer was incorrect. """

    def is_empty(self) -> bool:
        """ Check if this feedback item contains any actual feedback. """

        return ((self.general is None) and (self.correct is None) and (self.incorrect is None))

    @classmethod
    def from_raw_data(cls,
            raw_data: typing.Any,
            base_dir: typing.Union[str, None] = None,
            ) -> 'Feedback':
        """ Parse out feedback from one of several allowed forms. """

        if (raw_data is None):
            return Feedback()

        if (isinstance(str, raw_data)):
            parsed_text = quizcomp.parser.public.parse_text(raw_data, base_dir = base_dir)
            return Feedback(general = parsed_text)

        quizcomp.errors.check_type(raw_data, dict, "'feedback'")

        data: typing.Dict[str, typing.Any] = typing.cast(typing.Dict[str, typing.Any], raw_data)
        result = {}

        allowed_keys = ['general', 'correct', 'incorrect']
        actual_keys = list(data.keys())

        bad_keys = list(sorted(set(actual_keys) - set(allowed_keys)))
        if (len(bad_keys) > 0):
            raise quizcomp.errors.QuestionValidationError(
                    f"Unknown keys in feedback ({bad_keys}). Allowed keys: {allowed_keys}.",
                    base_dir = base_dir)

        for (key, value) in data.items():
            if (value is None):
                continue

            quizcomp.errors.check_type(value, str, f"'{key}' feedback value")

            value = str(value).strip()
            if (len(value) == 0):
                continue

            result[key] = quizcomp.parser.public.parse_text(value, base_dir = base_dir)

        return Feedback(**result)
