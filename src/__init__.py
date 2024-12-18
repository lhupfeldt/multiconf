# Copyright (c) 2012 - 2023 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from importlib.metadata import version  # type: ignore

# pylint: disable=unused-import

from .multiconf import McConfigRoot, AbstractConfigItem, ConfigItem, RepeatableConfigItem, DefaultItems, ConfigBuilder
from .decorators import mc_config
from .config_errors import ConfigException, ConfigDefinitionException, ConfigApiException, InvalidUsageException
from .config_errors import ConfigAttributeError, ConfigExcludedAttributeError, ConfigExcludedKeyError
from .config_errors import caller_file_line
from .values import MC_REQUIRED, MC_TODO, McInvalidValue, McTodoHandling


__all__ = [
    'mc_config', 'McConfigRoot', 'AbstractConfigItem', 'ConfigItem', 'RepeatableConfigItem', 'DefaultItems', 'ConfigBuilder',
    'ConfigException', 'ConfigDefinitionException', 'ConfigApiException', 'InvalidUsageException',
    'ConfigAttributeError', 'ConfigExcludedAttributeError',
    'MC_REQUIRED', 'MC_TODO', 'McInvalidValue', 'McTodoHandling',
]

__version__ = version("multiconf")
