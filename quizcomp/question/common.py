import quizcomp.common
import quizcomp.parser.public
import quizcomp.util.serial

class ParsedTextWithFeedback(quizcomp.parser.public.ParsedText):
    def __init__(self, parsed_text, feedback = None):
        super().__init__(parsed_text.text, parsed_text.document)

        if ((feedback is not None) and (not isinstance(feedback, quizcomp.parser.public.ParsedText))):
            raise quizcomp.common.QuizValidationError("Text feedback must be quizcomp.parser.public.ParsedText, found '%s'." % (str(type(feedback))))

        self.feedback = feedback

    def has_feedback(self):
        return (self.feedback is not None)

    def to_pod(self, skip_feedback = False, force_dict = False, **kwargs):
        if (skip_feedback or (self.feedback is None)):
            if (force_dict):
                return {'text': self.text}
            else:
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

    def __init__(self, parsed_text_with_feedback, correct):
        super().__init__(parsed_text_with_feedback, feedback = parsed_text_with_feedback.feedback)

        if (not isinstance(correct, bool)):
            raise quizcomp.common.QuizValidationError("Choice 'correct' field must be boolean, found '%s'." % (str(type(correct))))

        self.correct = correct

    def is_correct(self):
        return self.correct

    def to_pod(self, **kwargs):
        value = super().to_pod(force_dict = True, **kwargs)
        value['correct'] = self.correct
        return value

class NumericChoice(quizcomp.util.serial.PODSerializer):
    """
    Numeric choices have no parsed text (aside from optional feedback).
    """

    def __init__(self, type, margin = None, min = None, max = None, value = None, precision = None, feedback = None):
        self.type = type
        self.margin = margin
        self.min = min
        self.max = max
        self.value = value
        self.precision = precision

        if ((feedback is not None) and (not isinstance(feedback, quizcomp.parser.public.ParsedText))):
            raise quizcomp.common.QuizValidationError("Text feedback must be quizcomp.parser.public.ParsedText, found '%s'." % (str(type(feedback))))

        self.feedback = feedback

    def has_feedback(self):
        return (self.feedback is not None)

    def to_pod(self, skip_feedback = False, **kwargs):
        data = self.__dict__.copy()

        for (key, value) in list(data.items()):
            if (value is None):
                del data[key]

        if (skip_feedback and ('feedback' in data)):
            del data['feedback']

        if ('feedback' in data):
            data['feedback'] = data['feedback'].to_pod()

        return data
