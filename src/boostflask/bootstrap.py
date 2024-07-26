__author__ = 'deadblue'

import importlib
import inspect
import logging
import pkgutil
from typing import Generator, Union
from types import ModuleType

from flask import Flask

from .config import ConfigType, _config_var
from .pool import ObjectPool
from .view.base import BaseView
from ._utils import prepend_slash


_logger = logging.getLogger(__name__)


def _is_private_model(model_name: str) -> bool:
    for part in reversed(model_name.split('.')):
        if part.startswith('_'):
            return True
    return False


class Bootstrap:

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
        """
        Bootstrap a flask app.

        Args:
            app (Flask): Flask app.
        
        Keyword Args:
            conf (ConfigType | None): Configuration for app.
            url_prefix (str | None): URL prefix for all views.
        """
        self._op = ObjectPool()
        self._app = app

        self._app_conf = app_conf
        if url_prefix is not None and url_prefix != '':
            self._url_prefix = prepend_slash(url_prefix)

    def _scan_views(self, pkg: ModuleType) -> Generator[BaseView, None, None]:
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
                        yield self._op.get(member)
                elif isinstance(member, BaseView):
                    yield member

    def __enter__(self) -> Flask:
        # Push config
        if self._app_conf is not None:
            _config_var.set(self._app_conf)
        app_pkg = importlib.import_module(self._app.import_name)
        with self._app.app_context():
            for view_obj in self._scan_views(app_pkg):
                http_methods = view_obj.methods or ('GET', 'POST')
                # Add url prefix
                url_rule = prepend_slash(view_obj.url_rule)
                if self._url_prefix is not None:
                    url_rule = f'{self._url_prefix}{url_rule}'
                # Register to app
                self._app.add_url_rule(
                    rule=url_rule,
                    endpoint=view_obj.endpoint,
                    view_func=view_obj,
                    methods=http_methods
                )
                _logger.info('Mount view %r => [%s]', view_obj, url_rule)
        return self._app

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._op.close()