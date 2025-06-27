__author__ = 'deadblue'

from typing import Any, Dict, Type

from ._utils import to_snake


class ConfigManager: 

    _data: Dict[str, Any] | None

    def __init__(self, data: Dict[str, Any] | None) -> None:
        self._data = data

    def _get_module_config(self, mdl_name: str) -> Dict[str, Any] | None:
        if self._data is None:
            return None
        conf = self._data
        for key in mdl_name.split('.'):
            conf = conf.get(key, None)
            if conf is None or not isinstance(conf, dict):
                return None
        return conf

    def get_object_config(self, obj_cls: Type) -> Dict[str, Any] | None:
        mdl_conf = self._get_module_config(obj_cls.__module__)
        if mdl_conf is None:
            return None
        for key in [
            obj_cls.__name__, to_snake(obj_cls.__name__)
        ]:
            value = mdl_conf.get(key, None)
            if value is not None and isinstance(value, Dict):
                return value
        return None
