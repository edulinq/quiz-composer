import typing

import quizcomp.common
import quizcomp.parser.public
import quizcomp.util.serial

class ParsedTextWithFeedback(quizcomp.parser.public.ParsedText):
    """ Text that has been parsed along with any feedback attached to it. """

    def __init__(self,
            parsed_text: quizcomp.parser.public.ParsedText,
            feedback: typing.Union[quizcomp.parser.public.ParsedText, None] = None,
            ) -> None:
        super().__init__(parsed_text.text, parsed_text.document)

        self.feedback: typing.Union[quizcomp.parser.public.ParsedText, None] = feedback
        """ Feedback associated with this text. """

    def to_pod(self,
            skip_feedback: bool = False,
            force_dict: bool = False,
            **kwargs: typing.Any,
            ) -> quizcomp.util.serial.POD:  # type: ignore[override]
        if (skip_feedback or (self.feedback is None)):
            if (force_dict):
                return {'text': self.text}

            return self.text

        return {
            'text': self.text,
            'feedback': self.feedback.to_pod(),
        }

    @staticmethod
    def empty() -> 'ParsedTextWithFeedback':
        """ Get an empty ParsedTextWithFeedback. """

        return ParsedTextWithFeedback(quizcomp.parser.public.parse_text(''))

class ParsedTextChoice(ParsedTextWithFeedback):
    """
    A multiple answer/choice option.
    """

    def __init__(self,
            parsed_text_with_feedback: ParsedTextWithFeedback,
            correct: bool) -> None:
        super().__init__(parsed_text_with_feedback, feedback = parsed_text_with_feedback.feedback)

        self.correct: bool = correct
        """ Whether this choice is correct. """

    def is_correct(self) -> bool:
        """ Check if this choice is correct. """

        return self.correct

    def to_pod(self, **kwargs: typing.Any) -> quizcomp.util.serial.POD:  # type: ignore[override] # pylint: disable=arguments-differ
        data = super().to_pod(force_dict = True, **kwargs)

        value = typing.cast(typing.Dict[str, typing.Any], data)
        value['correct'] = self.correct

        return value

class NumericChoice(quizcomp.util.serial.PODSerializer):
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
            feedback: typing.Union[quizcomp.parser.public.ParsedText, None] = None,
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

        self.feedback: typing.Union[quizcomp.parser.public.ParsedText, None] = feedback
        """ Feedback associated with this text. """

    def to_pod(self, skip_feedback: bool = False, **kwargs: typing.Any) -> quizcomp.util.serial.POD:  # type: ignore[override]
        data = self.__dict__.copy()

        for (key, value) in list(data.items()):
            if (value is None):
                del data[key]

        if (skip_feedback and ('feedback' in data)):
            del data['feedback']

        if ('feedback' in data):
            data['feedback'] = data['feedback'].to_pod()

        return data
