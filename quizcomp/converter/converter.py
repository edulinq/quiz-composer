import abc
import typing

import quizcomp.question.base
import quizcomp.quiz

class Converter(abc.ABC):
    """
    The base class for converting quizzes (variants) to different formats (e.g., HTML).
    """

    def __init__(self, answer_key: bool = False, **kwargs: typing.Any) -> None:
        super().__init__()

        self.answer_key: bool = answer_key
        """ If the generated output should be an answer key. """

    @abc.abstractmethod
    def convert_variant(self, variant: quizcomp.quiz.Variant, **kwargs: typing.Any) -> str:
        """ Convert the given variant to the converter's target format and return the converted artifact. """

    def convert_question(self, question: quizcomp.question.base.Question, **kwargs: typing.Any) -> str:
        """
        Convert a single question using a dummy quiz layout.
        """

        variant = quizcomp.quiz.Variant.get_dummy(question)
        return self.convert_variant(variant, **kwargs)
