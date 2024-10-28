__author__ = 'deadblue'

import importlib
import sys
from typing import Dict, Sequence, Type
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

def get_parent_module(mdl: ModuleType) -> ModuleType | None:
    dot_index = mdl.__name__.rfind('.')
    if dot_index < 0:
        return None
    parent_mdl_name = mdl.__name__[:dot_index]
    return load_module(parent_mdl_name)

def join_url_paths(paths: Sequence[str]) -> str:
    url_path = ''
    for path in paths:
        if path is None or path == '': continue
        if path.endswith('/'):
            path = path.rstrip('/')
        if not path.startswith('/'):
            url_path += f'/{path}'
        else:
            url_path += path
    return url_path


_MAGIC_URL_PATH = '__url_path__'


class ModuleUrlResolver:

    _cache: Dict[str, str]

    def __init__(self) -> None:
        self._cache = {}
    
    def get_url_path(self, mdl: ModuleType) -> str:
         # Get from cache
        cache_key = mdl.__name__
        if cache_key in self._cache:
            return self._cache.get(cache_key)
        # Resolve module url path
        url_path = getattr(mdl, _MAGIC_URL_PATH, '')
        parent_mdl = get_parent_module(mdl)
        if parent_mdl is not None:
            url_path = join_url_paths([
                self.get_url_path(parent_mdl), url_path
            ])
        # Save to cache
        self._cache[cache_key] = url_path
        return url_path
