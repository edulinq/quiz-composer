import edq.util.serial

class Option:
    """
    This class makes it easier to access configuration values in core types for known options (attributes, hints, or style).
    These values are always keyed by strings, making them resistant to version changes.
    All information for accessing the known configuration are stored in this class.
    """

    def __init__(self,
            value_type: str,
            key: str,
            default_value: typing.Union[edq.util.serial.POD, None] = None,
            ) -> None:
        self.value_type: str = value_type
        """ Where to look within the core object for the configuration. """

        self.key: str = key
        """ The key for the value. """

        self.default_value = default_value
        """ The default value to use if the key is not present. """

OPTION_CUSTOM_HEADER: Option = Option('attributes', 'custom_header', None)
"""
A custom header for some object like a question, this would be used instead of something generic like "Question 4".

Defaults to nothing.
"""

OPTION_PICK_WITH_REPLACEMENT: str = Option('attributes', 'pick_with_replacement', True)
"""
Whether or not questions are chosen with replacement between variants.
True means that different variants can have the same questions.
False means that they cannot, but can also cause a warning if not enough questions are available in a group.

Defaults to true.
"""

OPTION_SHUFFLE_ANSWERS: Option = Option('attributes', 'shuffle_answers', True)
"""
If the answers in a question should be shuffled.

Defaults to true.
"""

OPTION_SKIP_NUMBERING_KEY: Option = Option('attributes', 'skip_numbering', False)
"""
If numbering for questions should be skipped.

Defaults to false.
"""
