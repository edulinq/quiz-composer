import typing

TYPE_PROJECT: str = 'project'
TYPE_QUIZ: str = 'quiz'
TYPE_QUESTION: str = 'question'
TYPE_VARIANT: str = 'variant'

JSON_OBJECT_TYPES: typing.List[str] = [TYPE_PROJECT, TYPE_QUIZ, TYPE_QUESTION, TYPE_VARIANT]

PROJECT_FILENAME: str = 'project.json'
QUIZ_FILENAME: str = 'quiz.json'
QUESTION_FILENAME: str = 'question.json'
PROMPT_FILENAME: str = 'prompt.md'

FORMAT_CANVAS: str = 'canvas'
FORMAT_HTML: str = 'html'
FORMAT_JSON: str = 'json'
FORMAT_MD: str = 'md'
FORMAT_TEX: str = 'tex'
FORMAT_TEXT: str = 'text'
FORMAT_QTI: str = 'qti'

# A special format mainly for testing.
FORMAT_JSON_TEMPLATE: str = 'json_template'

# Output formats.
DOC_FORMATS: typing.List[str] = [FORMAT_CANVAS, FORMAT_HTML, FORMAT_JSON, FORMAT_TEX, FORMAT_QTI]

# Formats that the parser understands basic conversions to.
PARSER_FORMATS: typing.List[str] = [FORMAT_CANVAS, FORMAT_HTML, FORMAT_JSON, FORMAT_MD, FORMAT_TEX, FORMAT_TEXT]

NUMERICAL_ANSWER_TYPE_EXACT: str = 'exact'
NUMERICAL_ANSWER_TYPE_RANGE: str = 'range'
NUMERICAL_ANSWER_TYPE_PRECISION: str = 'precision'
