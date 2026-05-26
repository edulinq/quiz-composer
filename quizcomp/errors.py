import typing

import edq.util.json

# TEST - Improve error output when a context is present.

# TEST - Accept context or core type? Or just serialization context? Or both?
#      - We just want something that responds to base_dir and/or source_path. Use prototype?

class ContextObject(typing.Protocol):
    base_dir: typing.Union[str, None]
    """ The base directory used when processing something the lead to an error. """

    source_path: typing.Union[str, None]
    """ The path being processed when an error occurred. """

class QuizValidationError(ValueError):
    """ An error that comes up when validating a quiz element. """

    def __init__(self,
            message: str,
            context: typing.Union[ContextObject, None] = None,
            base_dir: typing.Union[str, None] = None,
            **kwargs: typing.Any) -> None:
        self.context: typing.Union[ContextObject, None] = context
        """ The context that this error occurred within. """

        self.base_dir: typing.Union[str, None] = base_dir
        """ Context for where the error came from. """

        extra_info = {}

        if ((self.context is not None) and (self.context.base_dir is not None)):
            extra_info['base_dir'] = self.context.base_dir

        if ((self.context is not None) and (self.context.source_path is not None)):
            extra_info['source_path'] = self.context.source_path

        if (self.base_dir is not None):
            extra_info['base_dir'] = self.base_dir

        if (len(extra_info) > 0):
            message = f"{message} (Additional Context: {edq.util.json.dumps(extra_info)})"

        super().__init__(message)

class QuestionValidationError(QuizValidationError):
    """ An error that comes up when validating a question. """

    def __init__(self, message: str, **kwargs: typing.Any) -> None:
        super().__init__(message, **kwargs)

def check_type(
        value: typing.Any,
        expected_type: typing.Type,
        label: str,
        context: typing.Union[ContextObject, None] = None,
        base_dir: typing.Union[str, None] = None,
        ) -> None:
    """ Check that the given value has the expected type. """

    if (isinstance(value, expected_type)):
        return

    raise QuestionValidationError(
            f"{label} must be of type '{expected_type}', found '{value}' of type ({type(value)}).",
            context = context,
            base_dir = base_dir)
