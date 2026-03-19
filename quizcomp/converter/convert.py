import typing

import quizcomp.constants
import quizcomp.converter.converter
import quizcomp.converter.html
import quizcomp.converter.json
import quizcomp.converter.markdown
import quizcomp.converter.tex
import quizcomp.converter.qti
import quizcomp.question.base
import quizcomp.quiz

SUPPORTED_FORMATS: typing.List[str] = [
    quizcomp.constants.FORMAT_CANVAS,
    quizcomp.constants.FORMAT_HTML,
    quizcomp.constants.FORMAT_JSON,
    quizcomp.constants.FORMAT_MD,
    quizcomp.constants.FORMAT_TEX,
    quizcomp.constants.FORMAT_QTI,
]

# Formats for testing only.
TEST_SUPPORTED_FORMAT: typing.List[str] = [
    quizcomp.constants.FORMAT_JSON_TEMPLATE,
]

def get_converter_class(format: str = quizcomp.constants.FORMAT_JSON) -> typing.Type[quizcomp.converter.converter.Converter]:
    """ Get the converter class for the specified format. """

    if (format == quizcomp.constants.FORMAT_JSON):
        return quizcomp.converter.json.JSONConverter
    elif (format == quizcomp.constants.FORMAT_HTML):
        return quizcomp.converter.html.HTMLTemplateConverter
    elif (format == quizcomp.constants.FORMAT_CANVAS):
        return quizcomp.converter.html.CanvasTemplateConverter
    elif (format == quizcomp.constants.FORMAT_MD):
        return quizcomp.converter.markdown.MarkdownTemplateConverter
    elif (format == quizcomp.constants.FORMAT_TEX):
        return quizcomp.converter.tex.TexTemplateConverter
    elif (format == quizcomp.constants.FORMAT_QTI):
        return quizcomp.converter.qti.QTITemplateConverter
    elif (format == quizcomp.constants.FORMAT_JSON_TEMPLATE):
        return quizcomp.converter.json.JSONTemplateConverter
    else:
        raise ValueError(f"No known converter for format '{format}'.")

def get_converter(format: str = quizcomp.constants.FORMAT_JSON, **kwargs: typing.Any) -> quizcomp.converter.converter.Converter:
    """ Get the converter for the specified format. """

    converter_class = get_converter_class(format = format)
    return converter_class(**kwargs)

def convert_variant(
        variant: quizcomp.quiz.Variant,
        format: str = quizcomp.constants.FORMAT_JSON,
        constructor_args: typing.Union[typing.Dict[str, typing.Any], None] = None,
        converter_args: typing.Union[typing.Dict[str, typing.Any], None] = None,
        ) -> str:
    """ Convert a variant to the given format. """

    if (constructor_args is None):
        constructor_args = {}

    if (converter_args is None):
        converter_args = {}

    if (not isinstance(variant, quizcomp.quiz.Variant)):
        raise ValueError(f"convert_variant() requires a quizcomp.quiz.Variant type, found {type(variant)}.")

    converter = get_converter(format = format, **constructor_args)
    return converter.convert_variant(variant, **converter_args)

def convert_question(
        question: quizcomp.question.base.Question,
        format: str = quizcomp.constants.FORMAT_JSON,
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
