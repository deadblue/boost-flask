__author__ = 'deadblue'

from abc import ABC
from contextlib import AbstractContextManager


class Context(AbstractContextManager, ABC):
    """
    Base class for custom context.

    All subclass instances will be entered when request starts, and will be 
    exited when request teardowns.
    """

    order: int = 0
    """
    Context order, bigger one will be entered earlier, and existed later.
    """

    ...