__author__ = 'deadblue'

import inspect
import logging
import pkgutil
from typing import Any, Dict, List, Type
from types import ModuleType, TracebackType

from flask import Flask
from flask.typing import ResponseReturnValue

from .config import _put_config
from .context import (
    RequestContext, 
    _RequestContextManager,
    _current_manager
)
from .error_handler import ErrorHandler
from .pool import ObjectPool
from .view.base import BaseView
from ._utils import (
    ModuleUrlResolver,
    is_private_module,
    load_module,
    join_url_paths
)


_logger = logging.getLogger(__name__)


class Bootstrap:
    """Flask app bootstrap.

    Args:
        app (Flask): Flask app.
        app_conf (ConfigType | None): Configuration for app.
        url_prefix (str | None): URL prefix for all views.
    """

    _app: Flask
    _op: ObjectPool
    _ctx_types: List[Type[RequestContext]]
    
    _url_prefix: str | None = None

    def __init__(
            self, 
            app: Flask, 
            *,
            app_conf: Dict[str, Any] | None = None,
            url_prefix: str | None = None,
        ) -> None:
        # Save app
        self._app = app
        # Create object pool
        self._op = ObjectPool()
        self._op.init_app(app)
        # Context classes
        self._ctx_types = []
        # Put config
        if app_conf is not None:
            _put_config(app, app_conf)
        # Save global url prefix
        if url_prefix is not None:
            self._url_prefix = url_prefix

    def _register_view(self, url_prefix: str, view_obj: BaseView):
        url_rule = join_url_paths([
            url_prefix,  view_obj.url_rule
        ] if self._url_prefix is None else [
            self._url_prefix, url_prefix, view_obj.url_rule
        ])
        # Register to app
        self._app.add_url_rule(
            rule=url_rule,
            endpoint=view_obj.endpoint,
            view_func=view_obj,
            methods=view_obj.methods
        )
        _logger.info('Mount view %r => [%s]', view_obj, url_rule)

    def _scan_app_package(self, pkg: ModuleType):
        _logger.debug('Scanning views under package: %s', pkg.__name__)
        url_resolver = ModuleUrlResolver()
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
                    # Handle useful classes
                    if issubclass(member, BaseView):
                        view_obj = self._op.get(member)
                        self._register_view(url_resolver.get_url_path(mdl), view_obj)
                    elif issubclass(member, RequestContext):
                        self._ctx_types.append(member)
                    elif issubclass(member, ErrorHandler):
                        eh_obj = self._op.get(member)
                        self._app.register_error_handler(
                            eh_obj.error_class or Exception, eh_obj.handle
                        )
                elif isinstance(member, BaseView):
                    self._register_view(url_resolver.get_url_path(mdl), member)

    def __enter__(self) -> Flask:
        # Register event functions
        self._app.before_request(self._before_request)
        self._app.teardown_request(self._teardown_request)
        # Scan app package
        app_pkg = load_module(self._app.import_name)
        with self._app.app_context():
            self._scan_app_package(app_pkg)
        # Sort request context by order
        if len(self._ctx_types) > 0:
            self._ctx_types.sort(
                key=lambda c:c.order, reverse=True
            )
        return self._app

    def __exit__(
            self, 
            exc_type: Type[BaseException] | None, 
            exc_value: BaseException | None, 
            traceback: TracebackType | None
        ) -> None:
        # Remove event functions
        self._app.before_request_funcs.get(None).remove(self._before_request)
        self._app.teardown_request_funcs.get(None).remove(self._teardown_request)
        # TODO: Remove views which are registered in __enter__.
        # Close object pool
        self._op.close()

    def _before_request(self) -> ResponseReturnValue:
        if len(self._ctx_types) == 0: return
        req_ctx_mgr = _RequestContextManager()
        for ctx_type in self._ctx_types:
            req_ctx_mgr.add_context(self._op.create(ctx_type))
        req_ctx_mgr.__enter__()

    def _teardown_request(self, exc_value: BaseException | None) -> None:
        req_ctx_mgr = _current_manager()
        if req_ctx_mgr is not None:
            exc_type, tb = None, None
            if exc_value is not None:
                exc_type = type(exc_value)
                tb = exc_type.__traceback__
            req_ctx_mgr.__exit__(exc_type, exc_value, tb)
