import abc
import typing

import edq.util.serial

ATTR_CUSTOM_HEADER_KEY: str = 'custom_header'
""" An attribute for a custom header, instead of something generic like "Question 4". """

ATTR_CUSTOM_HEADER_DEFAULT: None = None
""" The default value for ATTR_CUSTOM_HEADER_KEY. """

ATTR_SHUFFLE_ANSWERS_KEY: str = 'shuffle_answers'
""" An attribute indicating if the answers in a question should be shuffled. """

ATTR_SHUFFLE_ANSWERS_DEFAULT: bool = True
""" The default value for ATTR_SHUFFLE_ANSWERS_KEY. """

ATTR_SKIP_NUMBERING_KEY: str = 'skip_numbering'
""" An attribute indicating if numbering for questions should be skipped. """

ATTR_SKIP_NUMBERING_DEFAULT: bool = False
""" The default value for ATTR_SKIP_NUMBERING_KEY. """

DEFAULT_AVAILABLE_POINTS: float = 0.0
""" The default available points for an object. """

class CoreType(edq.util.serial.DictConverter, abc.ABC):
    """
    The base class for concepts that are considered "core types" to the quiz composer.
    This includes things like quizzes, variants, groups, and questions.
    Core types are generally serializable and should be aware of their base dir (for path resolution).
    """

    def __init__(self,
            name: typing.Union[str, None] = None,
            parent: typing.Union[CoreType, None] = None,
            children: typing.Union[typing.List[CoreType], None] = None,
            points: typing.Union[float, None] = None,
            base_dir: str = '.',
            lms_id: typing.Union[str, None] = None,
            attributes: typing.Union[typing.Dict[str, edq.util.serial.POD], None] = None,
            hints: typing.Union[typing.Dict[str, edq.util.serial.POD], None] = None,
            style: typing.Union[typing.Dict[str, edq.util.serial.POD], None] = None,
            **kwargs: typing.Any) -> None:
        self.name: typing.Union[str, None] = name
        """
        The name of this object.
        If not specified, general names or names derived from parents will be used.
        """

        self.parent: typing.Union[CoreType, None] = parent
        """
        The parent/container for this object.
        The general pattern is: Quiz -> Variant -> Group -> Question.
        """

        if ((children is not None) and len(children) == 0):
            children = None

        self.children: typing.Union[typing.List[CoreType], None] = children
        """
        Children of this object.
        The general pattern is: Quiz -> Variant -> Group -> Question.
        """

        self.points: typing.Union[float, None] = points
        """
        The number of points associated with this object.
        This means different things depending on the context, e.g.,
        for a question it is the number of available points,
        and for a group it is the number of points for each question in the group.
        """

        self.base_dir: str = base_dir
        """ The base directory for any relative paths this object needs to resolve. """

        self.lms_id: typing.Union[str, None] = lms_id
        """ An ID to tie this object to an LMS (e.g. Moodle or Canvas). """

        if (attributes is None):
            attributes = {}

        self.attributes: typing.Dict[str, edq.util.serial.POD] = attributes.copy()
        """
        General attributes for this object.
        Attributes are well-defined configurations for objects.
        Attributes will always be observed (as long as the current version supports them).
        """

        if (hints is None):
            hints = {}

        self.hints: typing.Dict[str, edq.util.serial.POD] = hints.copy()
        """
        Hints for this objects.
        Hints generally affect layout for specific templates.
        Hints may be ignored.
        """

        if (style is None):
            style = {}

        self.style: typing.Dict[str, edq.util.serial.POD] = style.copy()
        """
        Styling rules for this object.
        Style may be defined in text or in JSON.
        """

    def get_available_points(self) -> float:
        """
        Get the total points available for this object.
        If the number of points is not explicitly set, parent objects may be consulted.
        If no point configuration can be found, DEFAULT_AVAILABLE_POINTS should be returned.
        """

        # First check self points.
        if (self.points is not None):
            return self.points

        # Then check the parent.
        if (self.parent is not None):
            return self.parent.get_child_points()

        # Finally, return default.
        return DEFAULT_AVAILABLE_POINTS

    def get_child_points(self) -> float:
        """
        Get the points available for a child of this object.
        By default, this is the number of available points divided evenly amongst the children.
        If no point configuration can be found, DEFAULT_AVAILABLE_POINTS should be returned.
        """

        split = 1
        if (self.children is not None):
            split = len(children)

        return self.get_available_points() / split

    def get_attribute(self, key: str, default_value: edq.util.serial.POD) -> edq.util.serial.POD:
        """
        Get an attribute value from this object or a parent.
        If the key does not exist (or the value is None), return the given default.
        """

        value = self._get_hierarchical_value('attributes', key)
        if (value is None):
            return default_value

        return value

    def get_hint(self, key: str, default_value: edq.util.serial.POD) -> edq.util.serial.POD:
        """
        Get a hint value from this object or a parent.
        If the key does not exist (or the value is None), return the given default.
        """

        value = self._get_hierarchical_value('hints', key)
        if (value is None):
            return default_value

        return value

    def get_style(self, key: str, default_value: edq.util.serial.POD) -> edq.util.serial.POD:
        """
        Get a style value from this object or a parent.
        If the key does not exist (or the value is None), return the given default.
        """

        value = self._get_hierarchical_value('style', key)
        if (value is None):
            return default_value

        return value

    def _get_hierarchical_value(self, value_type: str, key: str) -> typing.Union[edq.util.serial.POD, None]:
        """
        Get a value from either self or a parent (which may check its parent and so on).
        Return None if no value is found.
        """

        if (not hasattr(self, value_type)):
            raise ValueError(f"Unknown value type: '{value_type}'.")

        conainter = getattr(self, value_type)

        if (key in container):
            return container[key]

        if (self.parent is None):
            return None

        return self.parent._get_hierarchical_value(value_type, key)
