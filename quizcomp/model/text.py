import typing

import edq.util.serial

import quizcomp.parser.document

class ParsedText(edq.util.serial.DictConverter):
    """
    A representation of text that has been successfully parsed.
    """

    # Don't allow deserialization.
    _dictconverter_options = edq.util.serial.DictConverterOptions(
        allow_from_dict = False,
        skip_fields = {'document'},
    )

    def __init__(self,
            text: typing.Union[str, None] = None,
            document: typing.Union[quizcomp.parser.document.ParsedDocument, None] = None,
            ) -> None:
        if ((text is None) and (document is not None)):
            raise ValueError(f"Cannot supply a document without text: '{document}'.")

        if ((text is not None) and (document is None)):
            raise ValueError(f"Cannot supply text without a document: '{text}'.")

        if (text is None):
            text = ''

        self.text: str = text
        """ The cleaned text that was parsed. """

        if (document is None):
            document = quizcomp.parser.document.ParsedDocument()

        self.document = document
        """ The output of parsing. """

class ParsedTextWithFeedback(ParsedText):
    """ Text that has been parsed along with any feedback attached to it. """

    def __init__(self,
            parsed_text: typing.Union[ParsedText, None] = None,
            feedback: typing.Union[ParsedText, None] = None,
            ) -> None:
        if (parsed_text is None):
            super().__init__(text = None, document = None)
        else:
            super().__init__(text = parsed_text.text, document = parsed_text.document)

        self.feedback: typing.Union[ParsedText, None] = feedback
        """ Feedback associated with this text. """

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
