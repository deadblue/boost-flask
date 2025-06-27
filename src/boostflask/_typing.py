__author__ = 'deadblue'

from typing import (
    Any, Type, Tuple, Union, get_origin
)
from types import GenericAlias, UnionType


_GenericAlias2 = type(Tuple[int])
_UnionType2 = type(Union[int, str])


def _ensure_type(cls: Any) -> Type:
    if isinstance(cls, (GenericAlias, _GenericAlias2)):
        return get_origin(cls)
    return cls


def is_subclass(cls: Any, base_cls: Type | Tuple[Type, ...]) -> bool:
    if isinstance(cls, (GenericAlias, _GenericAlias2)):
        cls = _ensure_type(cls)
    if cls is None:
        return False
    return issubclass(cls, base_cls)


def is_instance(obj: Any, class_or_tuple: Any) -> bool:
    if isinstance(class_or_tuple, (GenericAlias, _GenericAlias2)):
        # Handle generic type
        class_or_tuple = _ensure_type(class_or_tuple)
    elif isinstance(class_or_tuple, (UnionType, _UnionType2)):
        # Handle union type
        class_or_tuple = Union[tuple([
            _ensure_type(cls) for cls in class_or_tuple.__args__
        ])]
    elif isinstance(class_or_tuple, tuple):
        # Handle type tuple
        class_or_tuple = tuple([
            _ensure_type(cls) for cls in class_or_tuple
        ])
    return isinstance(obj, class_or_tuple)
