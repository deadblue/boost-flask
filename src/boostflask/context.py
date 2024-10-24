__author__ = 'deadblue'

from abc import ABC
from contextlib import AbstractContextManager
from contextvars import ContextVar, Token
from typing import List, Type
from types import TracebackType


class RequestContext(AbstractContextManager, ABC):
    """
    Base class for custom context.

    All subclass instances will be entered when request starts, and will be 
    exited when request teardowns.
    """

    order: int = 0
    """
    Context order, bigger one will be entered earlier, and existed later.
    """

    ...


class _RequestContextManager(AbstractContextManager):

    _ctxs: List[RequestContext]
    _token: Token | None = None

    def __init__(self) -> None:
        self._ctxs = []
    
    def add_context(self, ctx: RequestContext):
        self._ctxs.append(ctx)

    def find_context(self, cls: Type[RequestContext]) -> RequestContext:
        for ctx in self._ctxs:
            if type(ctx) is cls:
                return ctx
        return None

    def __enter__(self):
        # Put manager to ContextVar
        self._token = _cv_manager.set(self)
        # Enter request contexts
        for ctx in self._ctxs:
            ctx.__enter__()

    def __exit__(
            self, 
            exc_type: type[BaseException] | None, 
            exc_value: BaseException | None, 
            tb: TracebackType | None
        ) -> None:
        # Exit request contexts in reversed order
        for ctx in reversed(self._ctxs):
            ctx.__exit__(exc_type, exc_value, tb)
        # Reset ContextVar
        _cv_manager.reset(self._token)


_cv_manager = ContextVar[_RequestContextManager]('boostflask.request_context_manager')


def _current_manager() -> _RequestContextManager | None:
    return _cv_manager.get(None)


def find_context(cls: Type[RequestContext]) -> RequestContext | None:
    manager = _current_manager()
    if manager is not None:
        return manager.find_context(cls)
    return None
