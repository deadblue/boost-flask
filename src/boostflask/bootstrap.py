__author__ = 'deadblue'

import inspect
import logging
import pkgutil
from typing import (
    Dict, Generator, Tuple, Union
)
from types import ModuleType


from flask import Flask

from .config import (
    ConfigType, put as put_config
)
from .pool import ObjectPool
from .view.base import BaseView
from ._utils import (
    is_private_module,
    load_module,
    get_parent_module,
    join_url_paths
)


_logger = logging.getLogger(__name__)


_MAGIC_URL_PATH = '__url_path__'

_module_url_path_cache: Dict[str, str] = {}

def _get_url_path(mdl: ModuleType) -> str:
    # Get from cache
    cache_key = mdl.__name__
    if cache_key in _module_url_path_cache:
        return _module_url_path_cache.get(cache_key)
    # Collect paths from modules
    paths = []
    m = mdl
    while m is not None:
        url_path = getattr(m, _MAGIC_URL_PATH, None)
        if url_path is not None:
            paths.append(url_path)
        m = get_parent_module(m)
    # Join paths
    url_path = join_url_paths(reversed(paths)) if len(paths) > 0 else ''
    # Put to cache
    _module_url_path_cache[cache_key] = url_path
    return url_path


class Bootstrap:
    """Flask app bootstrap.

    Args:
        app (Flask): Flask app.
        app_conf (ConfigType | None): Configuration for app.
        url_prefix (str | None): URL prefix for all views.
    """

    _op: ObjectPool
    _app: Flask

    _app_conf: Union[ConfigType, None] = None
    _url_prefix: Union[str, None] = None

    def __init__(
            self, app: Flask, 
            *,
            app_conf: Union[ConfigType, None] = None,
            url_prefix: Union[str, None] = None,
        ) -> None:
        self._op = ObjectPool()
        self._app = app

        self._app_conf = app_conf
        if url_prefix is not None:
            self._url_prefix = url_prefix

    def _scan_views(self, pkg: ModuleType) -> Generator[Tuple[str, BaseView], None, None]:
        _logger.debug('Scanning views under package: %s', pkg.__name__)
        for mi in pkgutil.walk_packages(
            path=pkg.__path__,
            prefix=f'{pkg.__name__}.'
        ):
            # Skip private module
            if is_private_module(mi.name): continue
            # Load module
            mdl = load_module(mi.name)
            _logger.debug('Scanning views under module: %s', mi.name)
            for name, member in inspect.getmembers(mdl):
                # Skip private member
                if name.startswith('_'): continue
                # Skip function
                if inspect.isfunction(member): continue
                # Handle class
                if inspect.isclass(member):
                    # Skip imported class
                    if member.__module__ != mi.name: continue
                    # Skip abstract class
                    if inspect.isabstract(member): continue
                    # Instantiate view and yield it
                    if issubclass(member, BaseView):
                        view_obj = self._op.get(member)
                        yield (_get_url_path(mdl), view_obj)
                elif isinstance(member, BaseView):
                    yield (_get_url_path(mdl), member)

    def __enter__(self) -> Flask:
        # Push config
        if self._app_conf is not None:
            put_config(self._app_conf)
        app_pkg = load_module(self._app.import_name)
        with self._app.app_context():
            for mdl_url_path, view_obj in self._scan_views(app_pkg):
                # Full URL rule
                url_rule = join_url_paths([
                    mdl_url_path,  view_obj.url_rule
                ] if self._url_prefix is None else [
                    self._url_prefix, mdl_url_path,  view_obj.url_rule
                ])
                # Register to app
                self._app.add_url_rule(
                    rule=url_rule,
                    endpoint=view_obj.endpoint,
                    view_func=view_obj,
                    methods=view_obj.methods
                )
                _logger.info('Mount view %r => [%s]', view_obj, url_rule)
        return self._app

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._op.close()