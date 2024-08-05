__author__ = 'deadblue'

import importlib
import sys
from typing import Sequence, Type, Union
from types import ModuleType


def get_class_name(cls: Type) -> str:
    return f'{cls.__module__}.{cls.__name__}'


def is_private_module(mdl_name: str) -> bool:
    for part in reversed(mdl_name.split('.')):
        if part.startswith('_'):
            return True
    return False

def load_module(mdl_name: str) -> ModuleType:
    mdl = sys.modules.get(mdl_name, None)
    if mdl is None:
        mdl = importlib.import_module(mdl_name)
    return mdl

def get_parent_module(mdl: ModuleType) -> Union[ModuleType, None]:
    dot_index = mdl.__name__.rfind('.')
    if dot_index < 0:
        return None
    parent_mdl_name = mdl.__name__[:dot_index]
    return load_module(parent_mdl_name)

def join_url_paths(paths: Sequence[str]) -> str:
    url_path = ''
    for path in paths:
        if path == '': continue
        if path.endswith('/'):
            path = path.rstrip('/')
        if not path.startswith('/'):
            url_path += f'/{path}'
        else:
            url_path += path
    return url_path