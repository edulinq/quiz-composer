import typing

import edq.util.serial

import quizcomp.errors
import quizcomp.parser.document

class Feedback(edq.util.serial.PODConverter):
    """
    Text that can be attached to objects (generally questions and answers) as a form of feedback for an action.
    Feedback can be specific to a correct/incorrect action, or just general.
    """

    serialization_omit_none = True
    serialization_omit_empty = True

    def __init__(self,
            general: typing.Union[quizcomp.parser.document.ParsedDocument, None] = None,
            correct: typing.Union[quizcomp.parser.document.ParsedDocument, None] = None,
            incorrect: typing.Union[quizcomp.parser.document.ParsedDocument, None] = None,
            **kwargs: typing.Any) -> None:
        if ((general is not None) and general.is_empty()):
            general = None

        self.general: typing.Union[quizcomp.parser.document.ParsedDocument, None] = general
        """ Feedback to be shown regardless of the outcome. """

        if ((correct is not None) and correct.is_empty()):
            correct = None

        self.correct: typing.Union[quizcomp.parser.document.ParsedDocument, None] = correct
        """ Feedback to be shown if the action/choice/answer was correct. """

        if ((incorrect is not None) and incorrect.is_empty()):
            incorrect = None

        self.incorrect: typing.Union[quizcomp.parser.document.ParsedDocument, None] = incorrect
        """ Feedback to be shown if the action/choice/answer was incorrect. """

    def collect_documents(self) -> typing.List[quizcomp.parser.document.ParsedDocument]:
        """ Collect all documents in this object. """

        documents = []

        if (self.general is not None):
            documents.append(self.general)

        if (self.correct is not None):
            documents.append(self.correct)

        if (self.incorrect is not None):
            documents.append(self.incorrect)

        return documents

    def is_empty(self) -> bool:
        """ Check if this feedback item contains any actual feedback. """

        return ((self.general is None) and (self.correct is None) and (self.incorrect is None))

    def _serialization_is_empty(self) -> bool:
        """ A special method for the serialization library to check. """

        return self.is_empty()

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        if (self.is_empty()):
            return None

        if ((self.general is not None) and (self.correct is None) and (self.incorrect is None)):
            return self.general.to_pod(context)

        return super().to_pod(context)

    @classmethod
    def from_raw_data(cls,
            raw_data: typing.Any,
            context: edq.util.serial.SerializationContext,
            ) -> 'Feedback':
        """ Parse out feedback from one of several allowed forms. """

        if (raw_data is None):
            return Feedback()

        if (isinstance(raw_data, str)):
            parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(raw_data, context)
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
                    context = edq.util.serial.SerializationContext)

        for (key, value) in data.items():
            if (value is None):
                continue

            quizcomp.errors.check_type(value, str, f"'{key}' feedback value")

            value = str(value).strip()
            if (len(value) == 0):
                continue

            result[key] = quizcomp.parser.document.ParsedDocument.parse_text(value, context)

        return Feedback(**result)
