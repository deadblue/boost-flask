__author__ = 'deadblue'

from typing import (
    Any, Type, Tuple,
    get_origin
)

def is_subclass(cls: Any, base_cls: Type | Tuple[Type, ...]) -> bool:
    if not isinstance(cls, Type):
        cls = get_origin(cls)
    if cls is None:
        return False
    return issubclass(cls, base_cls)
