import typing

import edq.util.serial

class CoreType(edq.util.serial.DictConverter):
    """
    The base class for concepts that are considered "core types" to the quiz composer.
    This includes things like quizzes, groups, and questions.
    Core types are generally serializable and should be aware of their base dir (for path resolution).
    """

    def __init__(self,
            base_dir: str = '.',
            lms_id: typing.Union[str, None] = None,
            **kwargs: typing.Any) -> None:
        self.base_dir: str = base_dir
        """ The base directory for any relative paths this object needs to resolve. """

        self.lms_id: typing.Union[str, None] = lms_id
        """ An ID to tie this object to an LMS (e.g. Moodle or Canvas). """

        # TEST
        # hints: typing.Union[typing.Dict[str, typing.Any], None] = None,
