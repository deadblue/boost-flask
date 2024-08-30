__author__ = 'deadblue'

from typing import (
    Any, Callable, ParamSpec, Type, TypeVar, Tuple
)

from .base import BaseView
from .renderer import (
    RendererType, 
    default as default_renderer
)
from .resolver import Resolver, StandardResolver


P = ParamSpec('P')
R = TypeVar('R')


class _FunctionView(BaseView):

    _handler: Callable[..., Any]
    _resolver: Resolver
    _renderer: RendererType

    def __init__(
            self, 
            url_rule: str,
            handler: Callable[..., Any],
            resolver: Resolver,
            renderer: RendererType = default_renderer
        ) -> None:
        self.url_rule = url_rule
        self._handler = handler
        self._resolver = resolver
        self._renderer = renderer

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        call_args = self._resolver.resolve_args(*args, **kwargs)
        result = self._handler(**call_args)
        return self._renderer(result)


def _make_endpoint_name(func: Callable) -> str:
    return f'{func.__module__}.{func.__qualname__}'.replace('.', '/')


def as_view(
        url_rule: str, 
        *, 
        methods: Tuple[str] | None = None,
        resolver_class: Type[Resolver] = StandardResolver,
        renderer: RendererType = default_renderer, 
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
            url_rule=url_rule,
            handler=func,
            resolver=resolver_class(func),
            renderer=renderer
        )
        fv.endpoint = _make_endpoint_name(func)
        if methods is not None and len(methods) > 0:
            fv.methods = methods
        return fv
    return view_creator
