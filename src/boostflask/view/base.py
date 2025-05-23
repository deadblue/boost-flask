__author__ = 'deadblue'

from abc import ABC, abstractmethod
from typing import (
    Any, ClassVar, Tuple, Type
)

from flask import Response

from .renderer import (
    RendererType, 
    default, json, html
)
from .resolver import (
    Resolver, StandardResolver
)


class BaseView(ABC):
    """
    BaseView is the parent class of View & FunctionView class.

    This class is used internally, developer's views should derive from View.
    """

    url_rule: str
    """
    Routing rule for the view.
    """

    endpoint: str
    """
    Endpoint name for the view.
    """

    methods: Tuple[str] = ('GET', 'HEAD', 'OPTIONS')
    """
    Handled request methods.
    """

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class View(BaseView, ABC):
    """
    Base view class for developer.
    """

    resolver_class: ClassVar[Type[Resolver]] = StandardResolver
    """
    Resolver class
    """

    _resolver: Resolver
    _renderer: RendererType

    def __init__(
            self, 
            url_rule: str,
            *,
            renderer: RendererType = default
        ) -> None:
        self.url_rule = url_rule
        self._renderer = renderer
        # Instantiate argument resolver
        self._resolver = self.resolver_class()
        self._resolver.parse_handler(self.handle)

        # Use full class name as endpoint
        cls = type(self)
        self.endpoint = f'{cls.__module__}_{cls.__name__}'.replace('.', '/')

    def __call__(self, *args: Any, **kwargs: Any) -> Response:
        call_args = self._resolver.resolve_args(*args, **kwargs)
        result = self.handle(**call_args)
        return self._renderer(result)

    @abstractmethod
    def handle(self, *args: Any, **kwargs: Any) -> Any: pass


class JsonView(View, ABC):

    def __init__(
            self, 
            url_rule: str
        ) -> None:
        super().__init__(
            url_rule=url_rule, 
            renderer=json
        )


class HtmlView(View, ABC):
    
    def __init__(
            self, 
            url_rule: str, 
            template_name: str
        ) -> None:
        super().__init__(
            url_rule=url_rule, 
            renderer=html(template_name)
        )
