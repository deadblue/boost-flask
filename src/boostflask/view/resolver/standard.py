__author__ = 'deadblue'

import logging
from typing import Any, Dict

from flask import request

from boostflask._typing import is_subclass
from .base import Resolver
from .types import RequestBody
from ._utils import (
    cast_value, snake_to_camel
)


_MIME_TYPE_URLENCODED_FORM = 'application/x-www-form-urlencoded'
_MIME_TYPE_MULTIPART_FORM = 'multipart/form-data'
_FORM_MIME_TYPES = {
    _MIME_TYPE_URLENCODED_FORM,
    _MIME_TYPE_MULTIPART_FORM
}

_logger = logging.getLogger(__name__)


class StandardResolver(Resolver):

    def resolve_args(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        handler_args_count = len(self._handler_args)
        # Fast-path
        if handler_args_count == 0:
            return {}
        # Resolve args from invoking arguments
        call_args = {}
        # Process positional arguments
        positional_args_count = 0
        if args is not None and len(args) > 0:
            positional_args_count = len(args)
            if positional_args_count > handler_args_count:
                _logger.warning(
                    'Incoming arguments is more than required: %d > %d',
                    positional_args_count, handler_args_count
                )
                positional_args_count = handler_args_count
            for index in range(positional_args_count):
                ha = self._handler_args[index]
                call_args[ha.name] = args[index]
        # Process keyword arguments
        if kwargs is not None and positional_args_count < handler_args_count:
            for ha in self._handler_args[positional_args_count:]:
                if ha.name in kwargs:
                    call_args[ha.name] = kwargs.get(ha.name)
        # Resolve missed arguments from request
        if len(call_args) != handler_args_count:
            self._resolve_args_from_request(call_args, positional_args_count)
        return call_args

    def _resolve_args_from_request(
            self, 
            call_args: Dict[str, Any], 
            skip_count: int
        ):
        # Parse HTTP form
        form = request.form if request.mimetype in _FORM_MIME_TYPES else {}
        # Fill call args
        for ha in self._handler_args[skip_count:]:
            # Skip already set argument
            if ha.name in call_args:
                continue
            # Handle special argument type
            if is_subclass(ha.type_, RequestBody):
                arg_value: RequestBody = ha.type_()
                arg_value.set_body(request.data)
                call_args[ha.name] = arg_value
                continue
            # Resolve argument from request
            arg_alias = snake_to_camel(ha.name)
            arg_value = None
            # Search from querystring
            if ha.name in request.args:
                arg_value = request.args.get(ha.name)
            elif arg_alias in request.args:
                arg_value = request.args.get(arg_alias)
            # Search from form
            if ha.name in form:
                arg_value = form.get(ha.name)
            elif arg_alias in form:
                arg_value = form.get(arg_alias)
            # Cast argument value
            if arg_value is not None:
                call_args[ha.name] = cast_value(arg_value, ha.type_)
            # TODO: Support files
