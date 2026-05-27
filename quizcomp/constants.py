import typing

QUIZ_FILENAME: str = 'quiz.json'
QUESTION_FILENAME: str = 'question.json'

FORMAT_CANVAS: str = 'canvas'
FORMAT_HTML: str = 'html'
FORMAT_JSON: str = 'json'
FORMAT_MD: str = 'md'
FORMAT_TEX: str = 'tex'
FORMAT_TEXT: str = 'text'
FORMAT_QTI: str = 'qti'

# Output formats.
DOC_FORMATS: typing.List[str] = [FORMAT_CANVAS, FORMAT_HTML, FORMAT_JSON, FORMAT_TEX, FORMAT_QTI]

# Formats that the parser understands basic conversions to.
PARSER_FORMATS: typing.List[str] = [FORMAT_CANVAS, FORMAT_HTML, FORMAT_JSON, FORMAT_MD, FORMAT_TEX, FORMAT_TEXT]

NUMERICAL_ANSWER_TYPE_EXACT: str = 'exact'
NUMERICAL_ANSWER_TYPE_RANGE: str = 'range'
NUMERICAL_ANSWER_TYPE_PRECISION: str = 'precision'
