# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '..'))

from multiconf import ConfigRoot, ConfigItem

class weblogic_config(ConfigRoot):
    def __init__(self, selected_env, valid_envs, **attr):
        super(weblogic_config, self).__init__(selected_env, valid_envs, **attr)

class admin_server(ConfigItem):
    def __init__(self, **attr):
        super(admin_server, self).__init__(repeat=False, server_type='admin', **attr)

class managed_server(ConfigItem):
    def __init__(self, **attr):
        super(managed_server, self).__init__(repeat=True, server_type='managed', **attr)

class datasource(ConfigItem):
    def __init__(self, **attr):
        super(datasource, self).__init__(repeat=True, **attr)
