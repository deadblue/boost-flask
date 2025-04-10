__author__ = 'deadblue'

import inspect
import logging
from typing import (
    Any, Dict, Protocol, Sequence, Type, TypeVar, 
    runtime_checkable
)

from flask import Flask, current_app

from ._utils import get_class_name


T = TypeVar('T')

_logger = logging.getLogger(__name__)


class TypelessArgumentError(Exception):

    def __init__(self, obj_type: Type, arg_name: str) -> None:
        message = f'{get_class_name(obj_type)} has a typeless argument: {arg_name}'
        super().__init__(message)


class CircularReferenceError(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@runtime_checkable
class Closeable(Protocol):

    def close(self) -> None: pass


_EXTENSION_NAME = 'flask_objectpool'


class ObjectPool:

    _registry: Dict[str, Any]

    def __init__(self) -> None:
        # Initialize registry
        self._registry = {}

    def init_app(self, app: Flask):
        # Register pool as flask extension
        app.extensions[_EXTENSION_NAME] = self

    def put(self, *objs: Any):
        """
        Manually put objects into to pool.

        Args:
            objs (Any): Object instances.
        """
        for obj in objs:
            key = get_class_name(type(obj))
            self._registry[key] = obj

    def get(self, obj_cls: Type[T]) -> T:
        """
        Lookup instance of given class, instantiate one when not found.

        Args:
            obj_cls (Type[T]): Object class.
        
        Returns:
            T: Object instance.
        """
        return self._lookup(obj_cls)

    def create(self, obj_cls: Type[T]) -> T:
        """
        Create instance of given class, without caching it.

        Args:
            obj_cls (Type[T]): Object class.

        Returns:
            T: Object instance.
        """
        return self._instantiate(obj_cls)

    def _lookup(
            self, 
            obj_cls: Type[T],
            dep_path: Sequence[str] | None = None
        ) -> T:
        cls_name = get_class_name(obj_cls)
        obj = self._registry.get(cls_name, None)
        if obj is None:
            obj = self._instantiate(obj_cls, dep_path)
            self._registry[cls_name] = obj
        return obj

    def _instantiate(
            self, 
            obj_cls: Type[T], 
            dep_path: Sequence[str] | None = None
        ) -> T:
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug('Instantiating object: %s', get_class_name(obj_cls))

        cls_name = get_class_name(obj_cls)
        if dep_path is not None and cls_name in dep_path:
            raise CircularReferenceError()

        init_spec = inspect.getfullargspec(obj_cls.__init__)
        required_args_num = len(init_spec.args) - 1
        if init_spec.defaults is not None:
            required_args_num -= len(init_spec.defaults)
        if required_args_num == 0:
            return obj_cls()

        next_dep_path = (cls_name, )
        if dep_path is not None:
            next_dep_path = dep_path + next_dep_path

        kwargs = {}
        for i in range(required_args_num):
            arg_name = init_spec.args[i+1]
            arg_cls = init_spec.annotations.get(arg_name, None)
            # TODO: Handle Union type
            if arg_cls is None:
                raise TypelessArgumentError(obj_cls, arg_name)
            else:
                kwargs[arg_name] = self._lookup(arg_cls, next_dep_path)
        return obj_cls(**kwargs)

    def close(self):
        for name, obj in self._registry.items():
            if isinstance(obj, Closeable):
                try:
                    obj.close()
                except:
                    _logger.warning('Close object %s failed ...', name)
        # Remove all objects
        self._registry.clear()


def current_pool() -> ObjectPool | None:
    """
    Return ObjectPool instance bound to current app.

    Returns:
        ObjectPool: ObjectPool instance.
    """
    return current_app.extensions.get(_EXTENSION_NAME, None)
