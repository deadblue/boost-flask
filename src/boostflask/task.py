__author__ = 'deadblue'

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, List, ParamSpec, Type, TypeVar

from .pool import ObjectPool, current_pool
from .context import BaseContext, _ContextManager


P = ParamSpec('P')
T = TypeVar('T')


class TaskExecutor:

    _ctx_types: List[Type[BaseContext]]

    _executor: ThreadPoolExecutor

    _pool: ObjectPool

    def __init__(self, pool: ObjectPool, max_workers: int = 8) -> None:
        self._pool = pool
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix='boostflask-worker'
        )
        self._ctx_types = []

    def add_context_type(self, ctx_type: Type[BaseContext]):
        self._ctx_types.append(ctx_type)

    def submit(self, fn: Callable[P, T], *args, **kwargs) -> Future[T]:
        return self._executor.submit(self._worker, fn, *args, **kwargs)

    def _worker(self, fn: Callable[P, T], *args, **kwargs) -> T:
        # Prepare contexts
        ctx_mgr = _ContextManager()
        for ctx_type in self._ctx_types:
            ctx_mgr.add_context(self._pool.create(ctx_type))
        with ctx_mgr:
            return fn(*args, **kwargs)

    def close(self):
        self._executor.shutdown(wait=True)

    @classmethod
    def current(cls) -> 'TaskExecutor':
        pool = current_pool()
        if pool is not None:
            return pool.get(TaskExecutor)
        return None


def as_task(fn: Callable[P, T]) -> Callable[P, Future[T]]:
    def wrapper(*args: Any, **kwargs: Any) -> Future[T]:
        te = TaskExecutor.current()
        if te is None:
            return None
        return te.submit(fn, *args, **kwargs)
    return wrapper
