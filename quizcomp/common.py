import typing

import edq.util.json

class QuizValidationError(ValueError):
    """ An error that comes up when validating a quiz element. """

    def __init__(self, message: str, ids: typing.Union[typing.Dict[str, str], None] = None, **kwargs: typing.Any) -> None:
        if (ids is None):
            ids = {}
        else:
            ids = ids.copy()

        ids.update(kwargs)

        parsed_ids = {}
        for (key, value) in ids.items():
            if ((value is None) or (value == '')):
                continue

            parsed_ids[str(key)] = value

        if (len(parsed_ids) > 0):
            message = f"{message} {edq.util.json.dumps(parsed_ids)}"

        super().__init__(message)

class QuestionValidationError(QuizValidationError):
    """ An error that comes up when validating a question. """

    def __init__(self, message: str, **kwargs: typing.Any) -> None:
        super().__init__(message, **kwargs)
