# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

# pylint: disable=unused-import
from .multiconf import ConfigRoot, ConfigItem, RepeatableConfigItem

major_version = sys.version_info[0]
if major_version < 3:
    from .multiconf_builder_py2 import ConfigBuilder
else:
    from .multiconf_builder_py3 import ConfigBuilder

from .config_errors import caller_file_line, ConfigException, ConfigDefinitionException, ConfigApiException, InvalidUsageException
from .values import MC_REQUIRED, MC_TODO
