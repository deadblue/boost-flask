__author__ = 'deadblue'

import logging

from boostflask import config

_logger = logging.getLogger(__name__)


class FooService:

    _bar: int

    def __init__(self) -> None:
        # Get config value
        self._bar = config.get('foo.bar')

    def get_bar(self) -> int:
        return self._bar

    def close(self):
        # Release resource when app shutdown
        _logger.info('Release resource in FooService ...')