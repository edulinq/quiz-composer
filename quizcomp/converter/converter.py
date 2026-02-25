import abc

import quizcomp.variant

class Converter(abc.ABC):
    def __init__(self, answer_key = False, **kwargs):
        super().__init__()

        self.answer_key = answer_key

    @abc.abstractmethod
    def convert_variant(self, variant, **kwargs):
        pass

    def convert_question(self, question, **kwargs):
        """
        Convert a single question using a dummy quiz layout.
        """

        variant = quizcomp.variant.Variant.get_dummy(question)
        return self.convert_variant(variant, **kwargs)
