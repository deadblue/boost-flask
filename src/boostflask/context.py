__author__ = 'deadblue'

from abc import ABC
from contextlib import AbstractContextManager
from contextvars import ContextVar, Token
from typing import List, Type, TypeVar
from types import TracebackType


class BaseContext(AbstractContextManager, ABC):
    """
    Base context class that will be entered before request or task starts, and 
    be exited after request or task ends.

    Context will be instantiated for each enter-exit loop, the instance will be
    released after loop.
    """

    order: int = 0
    """
    Context order, bigger one will be entered earlier, and existed later.
    """

    pass


class CommonContext(BaseContext, ABC):
    """
    Base class for common context that will be entered both in request and task.
    """
    pass


class RequestContext(BaseContext, ABC):
    """
    Base class for request-only context.
    """
    pass


class TaskContext(BaseContext, ABC):
    """
    Base class for task-only context.
    """
    pass


class _ContextManager(AbstractContextManager):

    _ctxs: List[BaseContext]
    _token: Token | None = None

    def __init__(self) -> None:
        self._ctxs = []
    
    def add_context(self, ctx: BaseContext):
        self._ctxs.append(ctx)

    def find_context(self, cls: Type[BaseContext]) -> BaseContext:
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

    @classmethod
    def current(cls) -> '_ContextManager':
        return _cv_manager.get(None)


_cv_manager = ContextVar[_ContextManager]('boostflask.context_manager')


ContextType = TypeVar('ContextType', bound=BaseContext)


def find_context(cls: Type[ContextType]) -> ContextType | None:
    """
    Find custom request context that is bound to current request.

    Args:
        cls (Type[ContextType]): Request context type.
    
    Returns:
        ContextType: Context instance or None.
    """
    manager = _ContextManager.current()
    if manager is not None:
        return manager.find_context(cls)
    return None
