import logging
import typing

import quizcomp.common

DEFAULT_CANVAS_OPTIONS: typing.Dict[str, typing.Any] = {
    'practice': True,
    'published': False,
    'hide_results': None,
    'show_correct_answers': True,
    'allowed_attempts': 1,
    'scoring_policy': 'keep_highest',
    'assignment_group_name': 'Quizzes',
}

ALLOWED_VALUES: typing.Dict[str, typing.List[typing.Any]] = {
    'practice': [True, False],
    'published': [True, False],
    'hide_results': [None, 'always', 'until_after_last_attempt'],
    'show_correct_answers': [True, False],
    'scoring_policy': ['keep_highest', 'keep_latest'],
}

def validate_options(old_options: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """ Validate Canvas options and return a clean version of the options. """

    options = DEFAULT_CANVAS_OPTIONS.copy()
    options.update(old_options)

    for (key, value) in options.items():
        if (key not in DEFAULT_CANVAS_OPTIONS):
            logging.warning("Unknown canvas options: '%s'.", key)
            continue

        if (key in ALLOWED_VALUES):
            if (value not in ALLOWED_VALUES[key]):
                raise quizcomp.common.QuizValidationError(
                        f"Canvas option '{key}' has value '{value}' not in allowed values: {ALLOWED_VALUES[key]}.")

        if (key == 'allowed_attempts'):
            options['allowed_attempts'] = _validate_allowed_attempts(value)

    return options

def _validate_allowed_attempts(allowed_attempts: typing.Any) -> int:
    """ Validate and fetch the number of allowed attempts. """

    if (not isinstance(allowed_attempts, (str, int))):
        raise quizcomp.common.QuizValidationError(f"Allowed attempts must be a positive int (or -1), found '{str(allowed_attempts)}'.")

    try:
        allowed_attempts = int(allowed_attempts)
    except:
        raise quizcomp.common.QuizValidationError(f"Allowed attempts must be a positive int (or -1), found '{str(allowed_attempts)}'.")  # pylint: disable=raise-missing-from

    if ((allowed_attempts < -1) or (allowed_attempts == 0)):
        raise quizcomp.common.QuizValidationError(f"Allowed attempts must be a positive int (or -1), found '{str(allowed_attempts)}'.")

    return allowed_attempts
