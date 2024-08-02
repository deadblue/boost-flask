__author__ = 'deadblue'

from typing import (
    Any, Callable, ParamSpec, Type, TypeVar, Tuple
)

from .base import BaseView
from .renderer import RendererType
from .resolver import Resolver, StandardResolver


P = ParamSpec('P')
R = TypeVar('R')


class _FunctionView(BaseView):

    _resolver: Resolver
    _renderer: RendererType

    def __init__(
            self, 
            handler: Callable[P, R],
            resolver: Resolver,
            renderer: RendererType
        ) -> None:
        self._handler = handler
        self._resolver = resolver
        self._renderer = renderer

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        call_args = self._resolver.resolve_args(*args, **kwargs)
        result = self._handler(**call_args)
        return self._renderer(result)


def _make_endpoint_name(func: Callable) -> str:
    return f'{func.__module__}.{func.__qualname__}'.replace('.', '_')


def as_view(
        url_rule: str, 
        renderer: RendererType, 
        *, 
        methods: Tuple[str] = ('GET', 'POST'),
        resolver_class: Type[Resolver] = StandardResolver
    ):
    """
    Wrap a function to view object that boostflask can mount.

    Args:
        url_rule (str): The URL rule to route to this view.
        renderer (RendererType): Response renderer.
        methods (Tuple[str]): Handled HTTP methods.
        resolver_class (Type[Resolver]): Arguments resolver class.
    """
    def view_creator(func: Callable[P, R]) -> _FunctionView:
        fv = _FunctionView(
            handler=func,
            resolver=resolver_class(func),
            renderer=renderer
        )
        fv.url_rule = url_rule
        fv.methods = methods
        fv.endpoint = _make_endpoint_name(func)
        return fv
    return view_creator
