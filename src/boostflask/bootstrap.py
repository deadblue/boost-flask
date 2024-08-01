__author__ = 'deadblue'

import importlib
import inspect
import logging
import pkgutil
from typing import Generator, Tuple, Union
from types import ModuleType

from flask import Flask

from .config import (
    ConfigType, put as put_config
)
from .pool import ObjectPool
from .view.base import BaseView
from ._utils import prepend_slash


_MAGIC_ATTR_URL_PREFIX = 'url_prefix'

_logger = logging.getLogger(__name__)


def _is_private_model(model_name: str) -> bool:
    for part in reversed(model_name.split('.')):
        if part.startswith('_'):
            return True
    return False


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
        if url_prefix is not None and url_prefix != '':
            self._url_prefix = prepend_slash(url_prefix)

    def _scan_views(self, pkg: ModuleType) -> Generator[Tuple[Union[str, None], BaseView], None, None]:
        _logger.debug('Scanning views under package: %s', pkg.__name__)
        for mi in pkgutil.walk_packages(
            path=pkg.__path__,
            prefix=f'{pkg.__name__}.'
        ):
            # Skip private model
            if _is_private_model(mi.name): continue
            # Load module
            mdl = importlib.import_module(mi.name)
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
                        mdl_url_prefix = getattr(mdl, _MAGIC_ATTR_URL_PREFIX, None)
                        yield (mdl_url_prefix, view_obj)
                elif isinstance(member, BaseView):
                    mdl_url_prefix = getattr(mdl, _MAGIC_ATTR_URL_PREFIX, None)
                    yield (mdl_url_prefix, member)

    def __enter__(self) -> Flask:
        # Push config
        if self._app_conf is not None:
            put_config(self._app_conf)
        app_pkg = importlib.import_module(self._app.import_name)
        with self._app.app_context():
            for mdl_url_prefix, view_obj in self._scan_views(app_pkg):
                # Add url prefix
                url_rule = prepend_slash(view_obj.url_rule)
                if mdl_url_prefix is not None:
                    url_rule = f'{prepend_slash(mdl_url_prefix)}{url_rule}'
                if self._url_prefix is not None:
                    url_rule = f'{self._url_prefix}{url_rule}'
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