__author__ = 'deadblue'

import inspect
import logging
from abc import ABC, abstractmethod
from typing import (
    Any, Callable, Dict, List, Type, TypeVar, Union
)
from types import UnionType, NoneType

from flask import request


T = TypeVar('T')

_MIME_TYPE_URLENCODED_FORM = 'application/x-www-form-urlencoded'
_MIME_TYPE_MULTIPART_FORM = 'multipart/form-data'
_FORM_MIME_TYPES = (
    _MIME_TYPE_URLENCODED_FORM,
    _MIME_TYPE_MULTIPART_FORM
)

_logger = logging.getLogger(__name__)


def _snake_to_camel(name: str) -> str:
    parts = name.split('_')
    if len(parts) == 1:
        return name
    return ''.join(map(
        lambda p:p[1] if p[0] == 0 else p[1].capitalize(),
        enumerate(parts)
    ))


def _cast_value(
        str_val: Union[str, None], 
        val_type: Union[Type[T], UnionType]
    ) -> Union[T, None]:
    if isinstance(val_type, UnionType):
        for inner_type in val_type.__args__:
            if inner_type is NoneType: continue
            return _cast_value(str_val, inner_type)
    if str_val is None:
        return None
    if val_type is None or val_type is str:
        return str_val
    elif val_type is int:
        return int(str_val, base=10)
    elif val_type is float:
        return float(str_val)
    elif val_type is bool:
        return str_val.lower() == 'true' or str_val == '1'
    return None


class Resolver(ABC):

    @abstractmethod
    def resolve_args(self, *args, **kwargs) -> Dict[str, Any]: pass


class _HandlerArg:

    name: str
    alias: str = None
    type_: Type

    def __init__(self, name: str, type_: Type) -> None:
        self.name = name
        self.alias = _snake_to_camel(name)
        self.type_ = type_


class StandardResolver(Resolver):

    _handler_args: List[_HandlerArg]
    _handler_args_count: int

    def __init__(self, handler: Callable) -> None:
        self._handler_args = []
        spec = inspect.getfullargspec(handler)
        for arg_name in spec.args:
            if arg_name == 'self': continue
            arg_type = spec.annotations.get(arg_name, None)
            self._handler_args.append(_HandlerArg(
                name=arg_name, type_=arg_type
            ))
        self._handler_args_count = len(self._handler_args)

    def resolve_args(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        # Fast-path
        if self._handler_args_count == 0:
            return {}
        # Resolve args from invoking arguments
        call_args = {}
        # Process positional arguments
        positional_args_count = 0
        if args is not None and len(args) > 0:
            positional_args_count = len(args)
            if positional_args_count > self._handler_args_count:
                _logger.warning(
                    'Incoming arguments is more than required: %d > %d',
                    positional_args_count, self._handler_args_count
                )
                positional_args_count = self._handler_args_count
            for index in range(positional_args_count):
                ha = self._handler_args[index]
                call_args[ha.name] = args[index]
        # Process keyword arguments
        if kwargs is not None and positional_args_count < self._handler_args_count:
            for ha in self._handler_args[positional_args_count:]:
                if ha.name in kwargs:
                    call_args[ha.name] = kwargs.get(ha.name)
        # Resolve missed arguments from request
        if len(call_args) != self._handler_args_count:
            self._resolve_args_from_request(call_args, positional_args_count)
        return call_args

    def _resolve_args_from_request(self, call_args: Dict[str, Any], skip_count:int):
        # Parse HTTP form
        form = request.form if request.mimetype in _FORM_MIME_TYPES else {}
        # Fill call args
        for ha in self._handler_args[skip_count:]:
            # Skip already set argument
            if ha.name in call_args: continue
            # Find argument from request
            arg_value = None
            # Search argument from querystring
            if ha.name in request.args:
                arg_value = request.args.get(ha.name)
            # Search argument alias from querystring
            elif ha.alias in request.args:
                arg_value = request.args.get(ha.alias)
            # Search argument from HTTP form
            if ha.name in form:
                arg_value = form.get(ha.name)
            # Search argument alias from HTTP form
            elif ha.alias in form:
                arg_value = form.get(ha.alias)
            if arg_value is not None:
                call_args[ha.name] = _cast_value(arg_value, ha.type_)
        # TODO: Support files & json
