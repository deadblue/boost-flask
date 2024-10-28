__author__ = 'deadblue'

from typing import Any
from boostflask.view import JsonView

__url_path__ = 'deep'
"""
BoostFlask magic attribute.
URL parent path for all views under this module.
"""

class View(JsonView):

    def __init__(self) -> None:
        super().__init__(
            url_rule = '/view'
        )
    
    def handle(self) -> Any:
        return {}