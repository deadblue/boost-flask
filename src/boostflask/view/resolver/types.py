__author__ = 'deadblue'

import json
from abc import ABC, abstractmethod
from typing import Any, Dict


class RequestBody(ABC):

    @abstractmethod
    def set_body(self, body: bytes) -> None: ...


class JsonBody(RequestBody):

    _json: Dict[str, Any]

    def set_body(self, body: bytes) -> None:
        self._json = json.loads(body)

    def get_json(self) -> Dict[str, Any]:
        return self._json
