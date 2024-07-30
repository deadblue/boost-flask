__author__ = 'deadblue'

from contextvars import ContextVar
from typing import Any, Dict


ConfigType = Dict[str, Any]

_config_var = ContextVar[ConfigType]('boostflask.config')

def put(value: ConfigType):
    _config_var.set(value)

def get_value(name: str, def_value: Any = None) -> Any:
    """
    Get config value

    Args:
        name (str): Config key
        def_value (Any): Default value when config not found
    
    Returns:
        Any: Config value.
    """
    conf_val = _config_var.get({})
    keys = name.split('.')
    for key in keys:
        if isinstance(conf_val, Dict):
            conf_val = conf_val.get(key, None)
        else:
            conf_val = getattr(conf_val, key, None)
        if conf_val is None:
            return def_value
    return conf_val
