import abc
import copy as pycopy
import datetime
import enum
import os
import typing

import edq.util.dirent
import edq.util.json

import quizcomp.common

POD: typing.TypeAlias = typing.Union[bool, float, int, str, typing.List['POD'], typing.Dict[str, 'POD']]  # pylint: disable=invalid-name
""" A "Plain Old Data" type that can be easily represented (e.g. in JSON). """

UNKNOWN_TYPE: str = '_unknown_'

class PODSerializer(abc.ABC):
    """ An abstract base for a class that can convert itselt for a POD type. """

    @abc.abstractmethod
    def to_pod(self, **kwargs: typing.Any) -> POD:
        """
        Create a "Plain Old Data" representation of this object.
        """

class JSONSerializer(PODSerializer):
    """
    A base class that can automatically handle serialization.
    Deserialization is harder (and requires validation),
    so will be left as abstract.
    """

    def __init__(self,
            type: str = UNKNOWN_TYPE,
            _skip_all_validation: bool = False,
            _skip_class_validations: typing.Union[typing.List[typing.Type], None] = None,
            **kwargs: typing.Any) -> None:
        self.type: str = type
        """ A marked type that can be useful for deserialization. """

        self._skip_all_validation: bool = _skip_all_validation
        """ Whether to skip all validation. """

        self._validated_classes: typing.Set[typing.Type] = set()
        """ A set of the classes that have been validated, so they can be skipped. """

        if (_skip_class_validations is not None):
            for cls in _skip_class_validations:
                self._validated_classes.add(cls)

    def validate(self, cls: typing.Union[typing.Type, None] = None, **kwargs: typing.Any) -> None:
        """
        A wrapper for validation.
        This should be called by child classes in their constructor.
        If cls is provided, then that specific _validate will be called.
        Otherwise, whatever default _validate() is registered for self's class will be called.
        This method should raise an exception if the object is invalid,
        and add `cls` to self._validated_classes if the object is valid.
        """

        if (self._skip_all_validation):
            return

        if (cls is None):
            cls = self.__class__

        if (cls in self._validated_classes):
            return

        cls._validate(self, **kwargs)
        self._validated_classes.add(cls)

    @abc.abstractmethod
    def _validate(self, **kwargs: typing.Any) -> None:
        """
        The true validation implementation.
        """

    def to_pod(self, **kwargs: typing.Any) -> POD:
        return self.to_dict(**kwargs)

    def to_dict(self, copy: bool = True, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
        """
        Convert self to a dictionary that can easily be serialized.
        See _serialize() for all the keyword arguments.
        """

        data = self.__dict__

        if (copy):
            data = pycopy.deepcopy(data)

        return _serialize(data, **kwargs)

    def to_json(self, indent: int = 4, sort_keys: bool = True, **kwargs: typing.Any) -> str:
        """ Serialize as a JSON string. """

        data = self.to_dict(**kwargs)
        return edq.util.json.dumps(data, indent = indent, sort_keys = sort_keys)

    def to_path(self, path: str, **kwargs: typing.Any) -> None:
        """ Write the JSON representation of this object to a file. """

        edq.util.dirent.write_file(path, self.to_json(**kwargs))

    @classmethod
    def from_dict(cls,
            data: typing.Dict[str, typing.Any],
            copy: bool = True,
            extra_fields: typing.Union[typing.Dict[str, typing.Any], None] = None,
            **kwargs: typing.Any) -> typing.Any:
        """ Construct an instance of this class from a dictionary (likely produced by to_dict()). """

        if (extra_fields is None):
            extra_fields = {}

        return _from_dict(cls, data, copy = copy, extra_fields = extra_fields, **kwargs)

    @classmethod
    def from_path(cls,
            path: str,
            add_base_dir: bool = True,
            data_callback: typing.Union[typing.Callable, None] = None,
            **kwargs: typing.Any,
            ) -> typing.Any:
        """ Construct an instance of this class from a JSON file. """

        path = os.path.abspath(path)
        ids = {
            'path': path,
        }

        if (not os.path.isfile(path)):
            raise quizcomp.common.QuizValidationError('Path does not exist or is not a file.', ids = ids)

        try:
            data = edq.util.json.load_path(path)
        except Exception as ex:
            raise quizcomp.common.QuizValidationError('Failed to read JSON file (invalid JSON?).', ids = ids) from ex

        base_dir = os.path.dirname(os.path.abspath(path))
        if (('base_dir' not in data) and add_base_dir):
            data['base_dir'] = base_dir

        if (data_callback is not None):
            data = data_callback(path, data)

        return cls.from_dict(data, copy = False, base_dir = base_dir, ids = ids, **kwargs)

def _from_dict(
        cls: typing.Type,
        data: typing.Dict[str, typing.Any],
        copy: bool = True,
        extra_fields: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any,
        ) -> typing.Any:
    """ Create an instance of the given class from a dictionary. """

    if (extra_fields is None):
        extra_fields = {}

    if (copy):
        data = pycopy.deepcopy(data)

    for (key, value) in extra_fields.items():
        data[key] = value

    return cls(**data)

def _serialize(
        item: typing.Any,
        skip_private: bool = True,
        convert_serializers: bool = True,
        convert_dates: bool = True,
        recursive: bool = True,
        **kwargs: typing.Any,
        ) -> typing.Any:
    """
    Generally convert an object into a form better suited to serialization.
    """

    kwargs['skip_private'] = skip_private
    kwargs['convert_serializers'] = convert_serializers
    kwargs['convert_dates'] = convert_dates
    kwargs['recursive'] = recursive

    if (isinstance(item, PODSerializer) and convert_serializers):
        return item.to_pod(**kwargs)
    elif (isinstance(item, enum.Enum)):
        return item.value
    elif (isinstance(item, list) and recursive):
        return [_serialize(value, **kwargs) for value in item]
    elif (isinstance(item, dict) and recursive):
        return {key: _serialize(value, **kwargs) for (key, value) in item.items() if (not (skip_private and key.startswith('_')))}
    elif (isinstance(item, (datetime.date, datetime.time, datetime.datetime)) and convert_dates):
        return item.isoformat()
    else:
        return item
