import enum
import typing

QUIZ_FILENAME: str = 'quiz.json'
QUESTION_FILENAME: str = 'question.json'

class Format(enum.Enum):
    """ Different formats that are available for output document or parser rendering. """

    CANVAS = 'canvas'
    HTML = 'html'
    JSON = 'json'
    MD = 'md'
    TEX = 'tex'
    TEXT = 'text'
    QTI = 'qti'

DOC_FORMATS: typing.List[Format] = [
    Format.CANVAS,
    Format.HTML,
    Format.JSON,
    Format.TEX,
    Format.QTI,
]
""" Format that can be used for output documents. """

PARSER_FORMATS: typing.List[Format] = [
    Format.CANVAS,
    Format.HTML,
    Format.JSON,
    Format.MD,
    Format.TEX,
    Format.TEXT,
]
""" Formats that the parser understands basic conversions to. """

class QuestionType(enum.Enum):
    """ The types of questions supported by the Quiz Composer. """

    ESSAY = 'essay'
    FIMB = 'fill_in_multiple_blanks'
    FITB = 'fill_in_the_blank'
    MATCHING = 'matching'
    MA = 'multiple_answers'
    MCQ = 'multiple_choice'
    MDD = 'multiple_dropdowns'
    NUMERICAL = 'numerical'
    SA = 'short_answer'
    TEXT_ONLY = 'text_only'
    TF = 'true_false'
