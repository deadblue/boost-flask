__author__ = 'deadblue'

import inspect
import logging
from typing import Any, Dict, Type, TypeVar, Union

from ._utils import get_class_name


T = TypeVar('T')

_logger = logging.getLogger(__name__)


class TypelessArgumentError(Exception):

    def __init__(self, obj_type: Type, arg_name: str) -> None:
        message = f'{get_class_name(obj_type)} has a typeless argument: {arg_name}'
        super().__init__(message)


class ObjectPool:

    _registry: Dict[str, Any]

    def __init__(self) -> None:
        # Initialize registry
        self._registry = {}

    def put(self, *objs: Any):
        """
        Manually put an object to pool.

        Args:
            objs (Any): Object instances.
        """
        for obj in objs:
            key = get_class_name(type(obj))
            self._registry[key] = obj

    def lookup(self, obj_cls: Type[T]) -> Union[T, None]:
        """
        Lookup object instance of given type, instantiate one when not found.

        Args:
            obj_cls (Type[T]): Object type.
        
        Returns:
            T: Object instance.
        """
        key = get_class_name(obj_cls)
        if key not in self._registry:
            self._registry[key] = self.instantiate(obj_cls)
        return self._registry.get(key, None)

    def instantiate(self, obj_cls: Type[T]) -> T:
        """
        Instatiate an object from type.

        Args:
            obj_cls (Type[T]): Object type.
        
        Returns:
            T: Object instance.
        """
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug('Instantiating object: %s', get_class_name(obj_cls))

        init_spec = inspect.getfullargspec(obj_cls.__init__)
        required_args_num = len(init_spec.args) - 1
        if init_spec.defaults is not None:
            required_args_num -= len(init_spec.defaults)
        if required_args_num == 0:
            return obj_cls()
        kwargs = {}
        for i in range(required_args_num):
            arg_name = init_spec.args[i+1]
            arg_type = init_spec.annotations.get(arg_name, None)
            if arg_type is None:
                raise TypelessArgumentError(obj_cls, arg_name)
            else:
                kwargs[arg_name] = self.lookup(arg_type)
        return obj_cls(**kwargs)

    def close(self):
        for name, obj in self._registry.items():
            close_method = getattr(obj, 'close', None)
            if close_method is None or not inspect.ismethod(close_method):
                continue
            try:
                close_method()
            except:
                _logger.warning('Call close failed for object: %s', name)
