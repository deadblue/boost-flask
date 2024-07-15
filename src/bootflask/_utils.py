__author__ = 'deadblue'

from typing import Type


def get_class_name(cls: Type) -> str:
    return f'{cls.__module__}.{cls.__name__}'
