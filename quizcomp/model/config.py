import typing

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

        if (self.value_type not in _known_options):
            _known_options[self.value_type] = {}

        _known_options[self.value_type][self.key] = self

_known_options: typing.Dict[str, typing.Dict[str, Option]] = {}
""" Keep track of all seen options, keyed by value type and then key. """

def get_known_option(key: str, value_type: typing.Union[str, None] = None) -> typing.Union[Option, None]:
    """
    Get a known option (if it exists).
    If no value type is provided, then search all types and return the first matching option.
    """

    if (value_type is not None):
        return _known_options.get(value_type, {}).get(key, None)

    for options in _known_options.values():
        if (key in options):
            return options[key]

    return None

OPTION_CUSTOM_HEADER: Option = Option('attributes', 'custom_header', None)
"""
A custom header for some object like a question, this would be used instead of something generic like "Question 4".

Defaults to nothing.
"""

OPTION_PICK_WITH_REPLACEMENT: Option = Option('attributes', 'pick_with_replacement', True)
"""
Whether or not questions are chosen with replacement between variants.
True means that different variants can have the same questions.
False means that they cannot, but can also cause a warning if not enough questions are available in a group.

Defaults to true.
"""

OPTION_POINT_PRECISION: Option = Option('attributes', 'point_precision', 2)
"""
The number of decimal places to use when displaying points.
The point value will first be rounded to this precision, and then formatted.

Defaults to 2.
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

OPTION_HINT_HEIGHT: Option = Option('hints', 'height', '4em')
"""
The height to use for this object.

Defaults to '4em'.
"""

OPTION_HINT_INLINE: Option = Option('hints', 'inline', False)
"""
If an object should try to render its content on the same line.

Defaults to false.
"""

OPTION_HINT_NOCENTER: Option = Option('hints', 'nocenter', False)
"""
Do not try to center for this object.

Defaults to false.
"""

OPTION_HINT_PAGEBREAK_AFTER: Option = Option('hints', 'pagebreak_after', False)
"""
If an object (usually a question) should insert a pagebreak after itself.

Defaults to false.
"""

OPTION_HINT_PAGEBREAK_BEFORE: Option = Option('hints', 'pagebreak_before', False)
"""
If an object (usually a question) should insert a pagebreak before itself.

Defaults to false.
"""

OPTION_HINT_WIDTH: Option = Option('hints', 'width', 1.0)
"""
The width to use for this object.

Defaults to 1,0.
"""
