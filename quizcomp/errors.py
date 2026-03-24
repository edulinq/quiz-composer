import typing

import quizcomp.model.base

class QuizValidationError(ValueError):
    """ An error that comes up when validating a quiz element. """

    def __init__(self,
            message: str,
            context_object: typing.Union[quizcomp.model.base.CoreType, None] = None,
            base_dir: typing.Union[str, None] = None,
            **kwargs: typing.Any) -> None:
        # TEST - Use context_object or base dir

        super().__init__(message)

        self.context_object: typing.Union[quizcomp.model.base.CoreType, None] = context_object
        """ The context_object that this error occurred within. """

        self.base_dir: typing.Union[str, None] = base_dir
        """ Context for where the error came from. """

class QuestionValidationError(QuizValidationError):
    """ An error that comes up when validating a question. """

    def __init__(self, message: str, **kwargs: typing.Any) -> None:
        super().__init__(message, **kwargs)

def check_type(
        value: typing.Any,
        expected_type: typing.Type,
        label: str,
        context_object: typing.Union[quizcomp.model.base.CoreType, None] = None,
        base_dir: typing.Union[str, None] = None,
        ) -> None:
    """ Check that the given value has the expected type. """

    if (isinstance(value, expected_type)):
        return

    raise quizcomp.errors.QuestionValidationError(
            f"{label} must be of type '{expected_type}', found '{value}' of type ({type(value)}).",
            context_object = context_object,
            base_dir = base_dir)
