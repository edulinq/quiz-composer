import enum

class QuestionType(enum.StrEnum):
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
