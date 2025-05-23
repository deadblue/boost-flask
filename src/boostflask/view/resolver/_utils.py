__author__ = 'deadblue'

from typing import Type, TypeVar
from types import UnionType, NoneType

T = TypeVar('T')


def snake_to_camel(name: str) -> str:
    parts = name.split('_')
    if len(parts) == 1:
        return name
    return ''.join(map(
        lambda p:p[1] if p[0] == 0 else p[1].capitalize(),
        enumerate(parts)
    ))


def cast_value(
        str_val: str | None, 
        val_type: Type[T] | UnionType
    ) -> T | None:
    # Unpack UnionType
    if isinstance(val_type, UnionType):
        for inner_type in val_type.__args__:
            if inner_type is NoneType: continue
            return cast_value(str_val, inner_type)
    if str_val is None:
        return None
    if val_type is None or val_type is str:
        return str_val
    elif val_type is int:
        return int(str_val, base=10)
    elif val_type is float:
        return float(str_val)
    elif val_type is bool:
        return str_val.lower() == 'true' or str_val == '1'
    return None
