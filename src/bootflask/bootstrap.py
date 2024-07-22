__author__ = 'deadblue'

import importlib
import inspect
import logging
import pkgutil
from typing import Generator, Union
from types import ModuleType

from flask import Flask

from ._pool import ObjectPool
from .config import ConfigType, _config_var
from .view.base import BaseView


_logger = logging.getLogger(__name__)


class Bootstrap:
    """
    Bootstrap a flask app.
    """

    _app: Flask
    _conf: Union[ConfigType, None]
    _op: ObjectPool

    def __init__(
            self, 
            app: Flask,
            conf: Union[ConfigType, None] = None
        ) -> None:
        """
        Args:
            app (Flask): Flask app.
            conf (ConfigType | None): Configuration for app.
        """
        self._app = app
        self._conf = conf
        self._op = ObjectPool()

    def _scan_views(self, pkg: ModuleType) -> Generator[BaseView, None, None]:
        _logger.debug('Scanning views under package: %s', pkg.__name__)
        for mi in pkgutil.walk_packages(
            path=pkg.__path__,
            prefix=f'{pkg.__name__}.'
        ):
            # Skip private package
            base_mdl_name = mi.name
            dot_index = base_mdl_name.rfind('.')
            if dot_index >= 0:
                base_mdl_name = base_mdl_name[dot_index+1:]
            if base_mdl_name.startswith('_'): continue
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
        if self._conf is not None:
            _config_var.set(self._conf)
        app_pkg = importlib.import_module(self._app.import_name)
        with self._app.app_context():
            for view_obj in self._scan_views(app_pkg):
                self._app.add_url_rule(
                    rule=view_obj.url_rule,
                    endpoint=view_obj.endpoint,
                    view_func=view_obj,
                    methods=view_obj.methods
                )
                _logger.info('Mount view %r => [%s]', view_obj, view_obj.url_rule)
        return self._app

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._op.close()