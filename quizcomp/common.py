import re
import quizcomp.util.json

# Plain String specification:
# ASCII alphanumerics + space + '_' + '-' + '.'
# No tabs/newlines, no leading/trailing spaces.
VALID_NAME_REGEX = re.compile(r'^[A-Za-z0-9 _\-\.]+$')

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

def validate_name(name, item_type="Name", allow_empty=False):
    if (not isinstance(name, str)):
        raise QuizValidationError(f"{item_type} must be a string. Got: {name!r}")

    if (name == ""):
        if (allow_empty):
            return
        raise QuizValidationError(f"{item_type} cannot be empty.")

    if (name != name.strip()):
        raise QuizValidationError(f"{item_type} cannot have leading or trailing spaces. Got: {name!r}")

    if (not VALID_NAME_REGEX.fullmatch(name)):
        raise QuizValidationError(f"{item_type} contains invalid characters. Allowed: A-Z, a-z, 0-9, space, _, -, and . Got: {name!r}")
