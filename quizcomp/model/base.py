import copy
import os
import typing

import edq.util.json
import edq.util.serial

import quizcomp.errors
import quizcomp.model.config
import quizcomp.parser.document

DEFAULT_AVAILABLE_POINTS: float = 0.0
""" The default available points for an object. """

class CoreType(edq.util.serial.DictConverter):
    """
    The base class for concepts that are considered "core types" to the quiz composer.
    This includes things like quizzes, variants, groups, and questions.
    Core types are generally serializable and should be aware of their base dir (for path resolution).
    """

    serialization_omit_none = True
    serialization_omit_empty = True
    serialization_error_class = quizcomp.errors.QuizValidationError
    serialization_skip_fields = [
        'base_dir',
        'parent',
        'source_path',
    ]

    def __init__(self,
            base_dir: typing.Union[str, None] = None,
            source_path: typing.Union[str, None] = None,
            name: typing.Union[str, None] = None,
            parent: typing.Union['CoreType', None] = None,
            children: typing.Union[typing.List['CoreType'], None] = None,
            points: typing.Union[float, None] = None,
            lms_id: typing.Union[str, None] = None,
            attributes: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            attributes_first: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            attributes_last: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            hints: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            hints_first: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            hints_last: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            style: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            style_first: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            style_last: typing.Union[typing.Dict[str, edq.util.serial.PODType], None] = None,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            **kwargs: typing.Any) -> None:
        if (base_dir is None):
            if (context is not None):
                base_dir = context.base_dir
            else:
                base_dir = '.'

        self.base_dir: str = os.path.abspath(base_dir)
        """ The base directory for any relative paths this object needs to resolve. """

        if ((source_path is None) and (context is not None)):
            source_path = context.source_path

        if ((source_path is not None) and (not os.path.isabs(source_path))):
            source_path = os.path.abspath(os.path.join(self.base_dir, source_path))

        self.source_path: typing.Union[str, None] = source_path
        """ If we are reading from a file, this attribute should be the absolute path to that file. """

        if ((name is not None) and (len(name) == 0)):
            name = None

        self.name: typing.Union[str, None] = name
        """
        The name of this object.
        If not specified, general names or names derived from parents will be used.
        """

        self.parent: typing.Union['CoreType', None] = parent
        """
        The parent/container fr this object.
        The general pattern is: Quiz -> Variant -> Group -> Question.
        """

        if (children is None):
            children = []

        self.children: typing.List['CoreType'] = children
        """
        Children of this object.
        The general pattern is: Quiz -> Variant -> Group -> Question.
        """

        # Set the parent of the childen to self.
        for child in self.children:
            child.parent = self

        if ((points is not None) and (points < 0)):
            raise quizcomp.errors.QuizValidationError(f"Points must be either null/None or non-negative, found: {points}.", context = self)

        self.points: typing.Union[float, None] = points
        """
        The number of points associated with this object.
        This means different things depending on the context, e.g.,
        for a question it is the number of available points,
        and for a group it is the number of points for each question in the group.
        """

        self.lms_id: typing.Union[str, None] = lms_id
        """ An ID to tie this object to an LMS (e.g. Moodle or Canvas). """

        if (attributes is None):
            attributes = {}

        attributes.update(kwargs)

        self.attributes: typing.Dict[str, edq.util.serial.PODType] = attributes.copy()
        """
        General attributes for this object.
        Attributes are well-defined configurations for objects.
        Attributes will always be observed (as long as the current version supports them).
        """

        if (attributes_first is None):
            attributes_first = {}

        self.attributes_first: typing.Dict[str, edq.util.serial.PODType] = attributes_first.copy()
        """ Attributes to pass along to the first child of this object. """

        if (attributes_last is None):
            attributes_last = {}

        self.attributes_last: typing.Dict[str, edq.util.serial.PODType] = attributes_last.copy()
        """ Attributes to pass along to the last child of this object. """

        if (hints is None):
            hints = {}

        self.hints: typing.Dict[str, edq.util.serial.PODType] = hints.copy()
        """
        Hints for this objects.
        Hints generally affect layout for specific templates.
        Hints may be ignored.
        """

        if (hints_first is None):
            hints_first = {}

        self.hints_first: typing.Dict[str, edq.util.serial.PODType] = hints_first.copy()
        """ Hints to pass along to the first child of this object. """

        if (hints_last is None):
            hints_last = {}

        self.hints_last: typing.Dict[str, edq.util.serial.PODType] = hints_last.copy()
        """ Hints to pass along to the last child of this object. """

        if (style is None):
            style = {}

        self.style: typing.Dict[str, edq.util.serial.PODType] = style.copy()
        """
        Styling rules for this object.
        Style may be defined in text or in JSON.
        """

        if (style_first is None):
            style_first = {}

        self.style_first: typing.Dict[str, edq.util.serial.PODType] = style_first.copy()
        """ Styles to pass along to the first child of this object. """

        if (style_last is None):
            style_last = {}

        self.style_last: typing.Dict[str, edq.util.serial.PODType] = style_last.copy()
        """ Styles to pass along to the last child of this object. """

    def get_name(self, default: str = '') -> str:
        """ Get the name of this object, using the default value if name is None. """

        if (self.name is None):
            return default

        return self.name

    def collect_documents(self) -> typing.List[quizcomp.parser.document.ParsedDocument]:
        """
        Collect documents for this object only (does not include any children).
        Use collect_all_documents() if you want child documents as well.
        """

        return []

    def collect_all_documents(self) -> typing.List[quizcomp.parser.document.ParsedDocument]:
        """ Collect all documents for this object and all children. """

        documents = self.collect_documents()
        for child in self.children:
            documents += child.collect_all_documents()

        return documents

    def get_points(self, check_children: bool = True) -> float:
        """
        Get the total points available for this object.

        This is computes as follows:
        1) If a value (`points` field) is explicitly set, then return that.
        2) If we have a parent, then ask them to compute points for is (via get_child_points()).
        3) If we have children, then sum up their points.
        4) Use DEFAULT_AVAILABLE_POINTS.
        """

        if (self.points is not None):
            return self.points

        if (self.parent is not None):
            return self.parent.get_child_points()

        if (check_children and (len(self.children) > 0)):
            total = 0.0
            for child in self.children:
                total += child.get_points()

            return total

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
            split = len(self.children)

        # Make sure to not try to use the children to compute the available points.
        return self.get_points(check_children = False) / split

    def get_display_points(self) -> str:
        """
        Return the output of get_points() rounded and formatted.
        """

        precision = int(self.get_config(quizcomp.model.config.OPTION_POINT_PRECISION))  # type: ignore[arg-type]

        points = self.get_points()

        if (precision <= 0):
            return str(int(points))

        points = round(points, precision)
        return str(points)

    def get_attribute(self, key: str, default_value: edq.util.serial.PODType) -> edq.util.serial.PODType:
        """
        Get an attribute value from this object or a parent.
        If the key does not exist (or the value is None), return the given default.
        """

        value = self._get_hierarchical_value('attributes', key)
        if (value is None):
            return default_value

        return value

    def get_hint(self, key: str, default_value: edq.util.serial.PODType) -> edq.util.serial.PODType:
        """
        Get a hint value from this object or a parent.
        If the key does not exist (or the value is None), return the given default.
        """

        value = self._get_hierarchical_value('hints', key)
        if (value is None):
            return default_value

        return value

    def get_style(self, key: str, default_value: edq.util.serial.PODType) -> edq.util.serial.PODType:
        """
        Get a style value from this object or a parent.
        If the key does not exist (or the value is None), return the given default.
        """

        value = self._get_hierarchical_value('style', key)
        if (value is None):
            return default_value

        return value

    def get_config(self,
            option: quizcomp.model.config.Option,
            default_override: typing.Union[edq.util.serial.PODType, None] = None,
            ) -> typing.Union[edq.util.serial.PODType, None]:
        """
        Get a value for a configuration option.
        If the key does not exist (or the value is None), return the specified default.

        Python callers should prefer this method, as mistakes can be caught by the type checker.
        """

        value = self._get_hierarchical_value(option.value_type, option.key)
        if (value is None):
            if (default_override is not None):
                return default_override

            return option.default_value

        return value

    def get_known_config(self,
            key: str,
            default_override: typing.Union[edq.util.serial.PODType, None] = None,
            value_type: typing.Union[str, None] = None,
            ) -> typing.Union[edq.util.serial.PODType, None]:
        """
        Get a value for a known configuration option by key.
        If the key does not exist (or the value is None), return the specified default.

        Non-Python callers will find this method useful.
        """

        option = quizcomp.model.config.get_known_option(key, value_type = value_type)
        if (option is None):
            return default_override

        return self.get_config(option, default_override = default_override)

    def _get_hierarchical_value(self, value_type: str, key: str,
            child: typing.Union['CoreType', None] = None,
            ) -> typing.Union[edq.util.serial.PODType, None]:
        """
        Get a value from either self or a parent (which may check its parent and so on).
        Return None if no value is found.

        If a value is passed for `child`, that value will be checked to see if it is the first or last child of this object,
        which will then prompt for checking in the `_first` and `_last` containers.
        `_first` and `_last` values will override base values.
        Only children will favor `_last` if both are present.

        The full order is: self, parent (first child), parent (last child), parent, gradnparent (first child), ...
        """

        if (not hasattr(self, value_type)):
            raise ValueError(f"Unknown value type: '{value_type}'.")

        container = getattr(self, value_type)

        found = False
        value = None

        # Check for the value normally.
        if (key in container):
            found = True
            value = container[key]

        # Check if the given child is present.
        if ((child is not None) and (child in self.children)):
            child_index = self.children.index(child)

            # Check if the child is a first.
            if (child_index == 0):
                context_container = getattr(self, value_type + '_first')
                if ((context_container is not None) and (key in context_container)):
                    found = True
                    value = context_container[key]

            # Check if the child is a last.
            if (child_index == (len(self.children) - 1)):
                context_container = getattr(self, value_type + '_last')
                if ((context_container is not None) and (key in context_container)):
                    found = True
                    value = context_container[key]

        if (found):
            return value

        # No value found here, and no parents.
        if (self.parent is None):
            return None

        # No value found here, check the parent (using ourself as the context child).
        return self.parent._get_hierarchical_value(value_type, key, child = self)

    def to_path(self,
            path: str,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> None:
        if (context is None):
            context = edq.util.serial.SerializationContext()

        context.json_options.setdefault('indent', 4)

        super().to_path(path, context)

    def copy(self, context: typing.Union[edq.util.serial.SerializationContext, None] = None) -> 'CoreType':
        return copy.deepcopy(self)
