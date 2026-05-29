import typing

import quizcomp.converter.converter
import quizcomp.converter.html
import quizcomp.converter.json
import quizcomp.converter.markdown
import quizcomp.converter.tex
import quizcomp.converter.qti
import quizcomp.model.constants
import quizcomp.model.question
import quizcomp.model.quiz

SUPPORTED_FORMATS: typing.List[quizcomp.model.constants.Format] = [
    quizcomp.model.constants.Format.CANVAS,
    quizcomp.model.constants.Format.HTML,
    quizcomp.model.constants.Format.JSON,
    quizcomp.model.constants.Format.MD,
    quizcomp.model.constants.Format.TEX,
    quizcomp.model.constants.Format.QTI,
]

def get_converter_class(
        format: quizcomp.model.constants.Format = quizcomp.model.constants.Format.JSON,
        ) -> typing.Type[quizcomp.converter.converter.Converter]:
    """ Get the converter class for the specified format. """

    if (format == quizcomp.model.constants.Format.JSON):
        return quizcomp.converter.json.JSONConverter
    elif (format == quizcomp.model.constants.Format.HTML):
        return quizcomp.converter.html.HTMLTemplateConverter
    elif (format == quizcomp.model.constants.Format.CANVAS):
        return quizcomp.converter.html.CanvasTemplateConverter
    elif (format == quizcomp.model.constants.Format.MD):
        return quizcomp.converter.markdown.MarkdownTemplateConverter
    elif (format == quizcomp.model.constants.Format.TEX):
        return quizcomp.converter.tex.TexTemplateConverter
    elif (format == quizcomp.model.constants.Format.QTI):
        return quizcomp.converter.qti.QTITemplateConverter
    else:
        raise ValueError(f"No known converter for format '{format.value}'.")

def get_converter(
        format: quizcomp.model.constants.Format = quizcomp.model.constants.Format.JSON,
        **kwargs: typing.Any,
        ) -> quizcomp.converter.converter.Converter:
    """ Get the converter for the specified format. """

    converter_class = get_converter_class(format = format)
    return converter_class(**kwargs)

def convert_variant(
        variant: quizcomp.model.quiz.Variant,
        format: quizcomp.model.constants.Format = quizcomp.model.constants.Format.JSON,
        constructor_args: typing.Union[typing.Dict[str, typing.Any], None] = None,
        converter_args: typing.Union[typing.Dict[str, typing.Any], None] = None,
        ) -> str:
    """ Convert a variant to the given format. """

    if (constructor_args is None):
        constructor_args = {}

    if (converter_args is None):
        converter_args = {}

    if (not isinstance(variant, quizcomp.model.quiz.Variant)):
        raise ValueError(f"convert_variant() requires a quizcomp.model.quiz.Variant type, found {type(variant)}.")

    converter = get_converter(format = format, **constructor_args)
    return converter.convert_variant(variant, **converter_args)

def convert_question(
        question: quizcomp.model.question.Question,
        format: quizcomp.model.constants.Format = quizcomp.model.constants.Format.JSON,
        constructor_args: typing.Union[typing.Dict[str, typing.Any], None] = None,
        converter_args: typing.Union[typing.Dict[str, typing.Any], None] = None,
        ) -> str:
    """ Convert a question to the given format. """

    if (constructor_args is None):
        constructor_args = {}

    if (converter_args is None):
        converter_args = {}

    converter = get_converter(format = format, **constructor_args)
    return converter.convert_question(question, **converter_args)
