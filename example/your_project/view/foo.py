__author__ = 'deadblue'


from typing import Any
from boostflask.view import JsonView

from your_project.service.foo import FooService


class IndexView(JsonView):

    _foo_service: FooService

    def __init__(
            self,
            foo_service: FooService
        ) -> None:
        super().__init__(
            url_rule = '/foo',
        )
        # Inject FooService
        self._foo_service = foo_service
    
    def handle(self) -> Any:
        return {
            'bar': self._foo_service.get_bar()
        }