__author__ = 'deadblue'

from typing import Any, Dict

from flask import Flask, current_app


_CONFIG_ROOT_NAME = 'BOOSTFLASK_CONFIG'


def _put_config(app: Flask, config: Dict[str, Any]):
    app.config[_CONFIG_ROOT_NAME] = config


def get(name: str, def_value: Any = None) -> Any:
    """
    Get config value.

    Args:
        name (str): Config key
        def_value (Any): Default value when config not found
    
    Returns:
        Any: Config value.
    """
    conf_val = current_app.config.get(_CONFIG_ROOT_NAME, {})
    keys = name.split('.')
    for key in keys:
        if isinstance(conf_val, Dict):
            conf_val = conf_val.get(key, None)
        else:
            conf_val = getattr(conf_val, key, None)
        if conf_val is None:
            return def_value
    return conf_val
