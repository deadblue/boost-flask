__author__ = 'deadblue'

import inspect
import logging
from typing import (
    Any, Dict, Protocol, Sequence, Type, TypeVar, 
    runtime_checkable
)

from flask import Flask, current_app

from ._config import ConfigManager
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

    _cm: ConfigManager
    _registry: Dict[str, Any]

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self._cm = ConfigManager(data=config)
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

        next_dep_path = (cls_name, )
        if dep_path is not None:
            next_dep_path = dep_path + next_dep_path

        # Prepare arguments for init method
        args, kwargs = [], {}
        obj_conf = self._cm.get_object_config(obj_cls)
        # Parse init method
        init_sign = inspect.signature(obj_cls.__init__)
        for index, (arg_name, spec) in enumerate(init_sign.parameters.items()):
            # Skip `self` argument
            if index == 0: continue
            if spec.kind in (spec.VAR_POSITIONAL, spec.VAR_KEYWORD): continue
            # Try config value first
            arg_value = None if obj_conf is None else obj_conf.get(arg_name, None)
            # Type-checking for argument value
            if arg_value is not None and \
                (spec.annotation is not spec.empty) and \
                (not isinstance(arg_value, spec.annotation)):
                arg_value = None
            if arg_value is None:
                # Skip argument with default value
                if spec.default is not spec.empty: continue
                # Prepare argument value
                if spec.annotation is spec.empty:
                    raise TypelessArgumentError(obj_cls, arg_name)
                elif issubclass(spec.annotation, ObjectPool):
                    arg_value = self
                else:
                    arg_value = self._lookup(spec.annotation, next_dep_path)
            # Put arg_value
            if spec.kind in (spec.POSITIONAL_ONLY, spec.POSITIONAL_OR_KEYWORD):
                args.append(arg_value)
            else:
                kwargs[arg_name] = arg_value
        return obj_cls(*args, **kwargs)

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
