__author__ = 'deadblue'

from typing import Any

from boostflask.view import JsonView


class HelloView(JsonView):

    def __init__(self) -> None:
        super().__init__(
            url_rule='/hello'
        )
    
    def handle(self, name: str = 'world') -> Any:
        return {
            'hello': name
        }
