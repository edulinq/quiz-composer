import quizcomp.util.json

class QuizValidationError(ValueError):
    def __init__(self, message, ids = {}, **kwargs):
        ids = ids.copy()
        ids.update(kwargs)

        parsed_ids = {}
        for (key, value) in ids.items():
            if ((value is None) or (value == '')):
                continue

            parsed_ids[str(key)] = value

        if (len(parsed_ids) > 0):
            message = "%s %s" % (message, quizcomp.util.json.dumps(parsed_ids))

        super().__init__(message)

class QuestionValidationError(QuizValidationError):
    def __init__(self, question, message, **kwargs):
        super().__init__(message, ids = question.ids, **kwargs)
