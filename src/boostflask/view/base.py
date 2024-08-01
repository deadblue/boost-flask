__author__ = 'deadblue'

from abc import ABC, abstractmethod
from typing import (
    Any, ClassVar, Optional, Tuple, Type
)

from flask import Response

from .renderer import (
    RendererType, json, html
)
from .resolver import (
    Resolver, StandardResolver
)


class BaseView(ABC):
    """
    BaseView is base class View & FunctionView class.
    """

    url_rule: str
    """
    Routing rule for the view.
    """

    endpoint: str
    """
    Endpoint name for the view.
    """

    methods: Tuple[str]
    """
    Allows request methods.
    """

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class View(BaseView, ABC):

    resolver_class: ClassVar[Type[Resolver]] = StandardResolver
    """
    Resolver class
    """

    _resolver: Resolver
    _renderer: RendererType

    def __init__(
            self, 
            url_rule: str,
            renderer: RendererType,
            methods: Optional[Tuple[str]] = None
        ) -> None:
        self.url_rule = url_rule
        self.methods = methods or ('GET', 'POST')
        self._renderer = renderer

        self._resolver = self.resolver_class(self.handle)

        # Use full class name as endpoint
        cls = type(self)
        self.endpoint = f'{cls.__module__}_{cls.__name__}'.replace('.', '_')

    def __call__(self, *args: Any, **kwargs: Any) -> Response:
        call_args = self._resolver.resolve_args(*args, **kwargs)
        result = self.handle(**call_args)
        return self._renderer(result)

    @abstractmethod
    def handle(self, *args: Any, **kwargs: Any) -> Any: pass


class JsonView(View, ABC):

    def __init__(
            self, 
            url_rule: str, 
            methods: Optional[Tuple[str]] = None,
        ) -> None:
        super().__init__(
            url_rule=url_rule, 
            renderer=json, 
            methods=methods
        )


class HtmlView(View, ABC):
    
    def __init__(
            self, 
            url_rule: str, 
            template_name: str, 
            methods: Optional[Tuple[str]] = None
        ) -> None:
        super().__init__(
            url_rule=url_rule, 
            renderer=html(template_name),
            methods=methods
        )
