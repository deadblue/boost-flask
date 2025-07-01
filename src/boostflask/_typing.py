__author__ = 'deadblue'

from typing import (
    Any, Tuple, Type, TypeVar, Union, get_origin
)
from types import GenericAlias, NoneType, UnionType


_GenericAlias2 = type(Tuple[int])
_UnionType2 = type(Union[int, str])

T = TypeVar('T')


def _ensure_type(cls: Any) -> Type:
    if isinstance(cls, (GenericAlias, _GenericAlias2)):
        return get_origin(cls)
    return cls


def is_subclass(cls: Any, base_cls: Type | Tuple[Type, ...]) -> bool:
    if cls is None:
        return False
    return issubclass(_ensure_type(cls), base_cls)


def is_instance(obj: Any, class_or_tuple: Any) -> bool:
    if isinstance(class_or_tuple, tuple):
        # Handle type tuple, e.g.: (str, int)
        class_or_tuple = tuple([
            _ensure_type(cls) for cls in class_or_tuple
        ])
    elif isinstance(class_or_tuple, (UnionType, _UnionType2)):
        # Handle union type, e.g.: str|int
        class_or_tuple = Union[tuple([
            _ensure_type(cls) for cls in class_or_tuple.__args__
        ])]
    else:
        # Handle generic type, e.g.: list[str]
        class_or_tuple = _ensure_type(class_or_tuple)
    return isinstance(obj, class_or_tuple)


def cast_value(
        val_str: str,
        val_type: Type[T] | UnionType,
    ) -> T | None:
    if isinstance(val_type, UnionType):
        for inner_type in val_type.__args__:
            if inner_type is NoneType: continue
            return cast_value(val_str, inner_type)
    if val_str is None:
        return None
    if val_type is None or val_type is str:
        return val_str
    elif val_type is int:
        return int(val_str, base=10)
    elif val_type is float:
        return float(val_str)
    elif val_type is bool:
        return val_str.lower() == 'true' or val_str == '1'
    return None