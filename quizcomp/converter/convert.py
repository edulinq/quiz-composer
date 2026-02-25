import quizcomp.constants
import quizcomp.converter.html
import quizcomp.converter.json
import quizcomp.converter.tex
import quizcomp.converter.qti
import quizcomp.variant

SUPPORTED_FORMATS = [
    quizcomp.constants.FORMAT_CANVAS,
    quizcomp.constants.FORMAT_HTML,
    quizcomp.constants.FORMAT_JSON,
    quizcomp.constants.FORMAT_TEX,
    quizcomp.constants.FORMAT_QTI,
]

# Formats for testing only.
TEST_SUPPORTED_FORMAT = [
    quizcomp.constants.FORMAT_JSON_TEMPLATE,
]

def get_converter_class(format = quizcomp.constants.FORMAT_JSON):
    if (format == quizcomp.constants.FORMAT_JSON):
        return quizcomp.converter.json.JSONConverter
    elif (format == quizcomp.constants.FORMAT_HTML):
        return quizcomp.converter.html.HTMLTemplateConverter
    elif (format == quizcomp.constants.FORMAT_CANVAS):
        return quizcomp.converter.html.CanvasTemplateConverter
    elif (format == quizcomp.constants.FORMAT_TEX):
        return quizcomp.converter.tex.TexTemplateConverter
    elif (format == quizcomp.constants.FORMAT_QTI):
        return quizcomp.converter.qti.QTITemplateConverter
    elif (format == quizcomp.constants.FORMAT_JSON_TEMPLATE):
        return quizcomp.converter.json.JSONTemplateConverter
    else:
        raise ValueError("No known converter for format '%s'." % (format))

def get_converter(format = quizcomp.constants.FORMAT_JSON, **kwargs):
    converter_class = get_converter_class(format = format)
    return converter_class(**kwargs)

def convert_variant(variant, format = quizcomp.constants.FORMAT_JSON,
        constructor_args = {}, converter_args = {}):
    if (not isinstance(variant, quizcomp.variant.Variant)):
        raise ValueError("convert_variant() requires a quizcomp.variant.Variant type, found %s." % (type(variant)))

    converter = get_converter(format = format, **constructor_args)
    return converter.convert_variant(variant, **converter_args)

def convert_question(question, format = quizcomp.constants.FORMAT_JSON,
        constructor_args = {}, converter_args = {}):
    converter = get_converter(format = format, **constructor_args)
    return converter.convert_question(question, **converter_args)
