import typing

import edq.util.json

import quizcomp.converter.converter
import quizcomp.model.quiz

class JSONConverter(quizcomp.converter.converter.Converter):
    """
    A converter to convert a quiz to JSON.
    The produced JSON will be more raw (less polished) than JSONTemplateConverter.
    """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def convert_variant(self, variant: quizcomp.model.quiz.Variant, **kwargs: typing.Any) -> str:
        return edq.util.json.dumps(variant.to_dict(), indent = 4)
