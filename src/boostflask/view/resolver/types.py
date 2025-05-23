__author__ = 'deadblue'

import json
from abc import ABC, abstractmethod
from typing import (
    Any, Dict, Type, 
    get_origin
)


class RequestBody(ABC):

    @abstractmethod
    def set_body(self, body: bytes) -> None: ...


def is_request_body_type(t: Any) -> bool:
    if not isinstance(t, Type):
        t = get_origin(t)
    if t is None:
        return False
    return issubclass(t, RequestBody)


class JsonBody(RequestBody):

    _json: Dict[str, Any]

    def set_body(self, body: bytes) -> None:
        self._json = json.loads(body)

    def get_json(self) -> Dict[str, Any]:
        return self._json
