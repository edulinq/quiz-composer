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

QUESTION_TYPE_ESSAY: str = 'essay'
QUESTION_TYPE_FIMB: str = 'fill_in_multiple_blanks'
QUESTION_TYPE_FITB: str = 'fill_in_the_blank'
QUESTION_TYPE_MATCHING: str = 'matching'
QUESTION_TYPE_MA: str = 'multiple_answers'
QUESTION_TYPE_MCQ: str = 'multiple_choice'
QUESTION_TYPE_MDD: str = 'multiple_dropdowns'
QUESTION_TYPE_NUMERICAL: str = 'numerical'
QUESTION_TYPE_SA: str = 'short_answer'
QUESTION_TYPE_TEXT_ONLY: str = 'text_only'
QUESTION_TYPE_TF: str = 'true_false'

# Supported question types.
QUESTION_TYPES: typing.List[str] = [
    QUESTION_TYPE_ESSAY,
    QUESTION_TYPE_FIMB,
    QUESTION_TYPE_FITB,
    QUESTION_TYPE_MATCHING,
    QUESTION_TYPE_MA,
    QUESTION_TYPE_MCQ,
    QUESTION_TYPE_MDD,
    QUESTION_TYPE_NUMERICAL,
    QUESTION_TYPE_SA,
    QUESTION_TYPE_TEXT_ONLY,
    QUESTION_TYPE_TF,
]

NUMERICAL_ANSWER_TYPE_EXACT: str = 'exact'
NUMERICAL_ANSWER_TYPE_RANGE: str = 'range'
NUMERICAL_ANSWER_TYPE_PRECISION: str = 'precision'
