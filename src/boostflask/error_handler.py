__author__ = 'deadblue'

from abc import ABC, abstractmethod
from typing import Type

from flask.typing import ResponseReturnValue


class ErrorHandler(ABC):

    error_class: Type[BaseException] | None = None
    """
    Error class which will be handled by this handler.

    Set it to None to handle all errors.
    """

    @abstractmethod
    def handle(self, exc: BaseException) -> ResponseReturnValue: ...
