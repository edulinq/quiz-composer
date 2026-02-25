TYPE_PROJECT = 'project'
TYPE_QUIZ = 'quiz'
TYPE_QUESTION = 'question'
TYPE_VARIANT = 'variant'

JSON_OBJECT_TYPES = [TYPE_PROJECT, TYPE_QUIZ, TYPE_QUESTION, TYPE_VARIANT]

PROJECT_FILENAME = 'project.json'
QUIZ_FILENAME = 'quiz.json'
QUESTION_FILENAME = 'question.json'
PROMPT_FILENAME = 'prompt.md'

FORMAT_CANVAS = 'canvas'
FORMAT_HTML = 'html'
FORMAT_JSON = 'json'
FORMAT_MD = 'md'
FORMAT_TEX = 'tex'
FORMAT_TEXT = 'text'
FORMAT_QTI = 'qti'

# A special format mainly for testing.
FORMAT_JSON_TEMPLATE = 'json_template'

# Output formats.
DOC_FORMATS = [FORMAT_CANVAS, FORMAT_HTML, FORMAT_JSON, FORMAT_TEX, FORMAT_QTI]

# Formats that the parser understands basic conversions to.
PARSER_FORMATS = [FORMAT_CANVAS, FORMAT_HTML, FORMAT_JSON, FORMAT_MD, FORMAT_TEX, FORMAT_TEXT]

QUESTION_TYPE_ESSAY = 'essay'
QUESTION_TYPE_FIMB = 'fill_in_multiple_blanks'
QUESTION_TYPE_FITB = 'fill_in_the_blank'
QUESTION_TYPE_MATCHING = 'matching'
QUESTION_TYPE_MA = 'multiple_answers'
QUESTION_TYPE_MCQ = 'multiple_choice'
QUESTION_TYPE_MDD = 'multiple_dropdowns'
QUESTION_TYPE_NUMERICAL = 'numerical'
QUESTION_TYPE_SA = 'short_answer'
QUESTION_TYPE_TEXT_ONLY = 'text_only'
QUESTION_TYPE_TF = 'true_false'

# Supported question types.
QUESTION_TYPES = [
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

NUMERICAL_ANSWER_TYPE_EXACT = 'exact'
NUMERICAL_ANSWER_TYPE_RANGE = 'range'
NUMERICAL_ANSWER_TYPE_PRECISION = 'precision'
