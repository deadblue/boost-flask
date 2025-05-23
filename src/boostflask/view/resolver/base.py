__author__ = 'deadblue'


import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any, Callable, Dict, List, Type
)


@dataclass
class HandlerArg:
    name: str
    type_: Type | None


class Resolver(ABC):

    _handler_args: List[HandlerArg]

    def parse_handler(self, handler: Callable):
        self._handler_args = []
        spec = inspect.getfullargspec(handler)
        for arg_name in spec.args:
            if arg_name == 'self': continue
            arg_type = spec.annotations.get(arg_name, None)
            self._handler_args.append(HandlerArg(
                name=arg_name, type_=arg_type
            ))

    @abstractmethod
    def resolve_args(self, *args, **kwargs) -> Dict[str, Any]: pass
