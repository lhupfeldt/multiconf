# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from multiconf.decorators import nested_repeatables, required


# Here we define what can be repeated within the configuration item. In this case
# we will have many managed servers and datasources.
# All simple properties must be defined in __init__, if not sane dafault exists, then the value MC_REQUIRED should be assigned
# Multiconf will verify that all such values are replaced with proper values before the full configuration is loaded
@nested_repeatables('managed_servers, datasources')
class weblogic_config(ConfigRoot):
    ''' This is just a simple holder of managed_servers and datasources '''
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                 mc_allow_todo=False, mc_allow_current_env_todo=False,
                 base_port=MC_REQUIRED):
        super(weblogic_config, self).__init__(
            selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
            mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
        self.base_port = base_port


# Weblogic's standalone administration server. Used to control domain.
class admin_server(ConfigItem):
    def __init__(self, host, port):
        super(admin_server, self).__init__()
        self.host = host
        self.port = port
        self.name = 'admin'
        self.server_type = 'admin'


# Here specify that a managed_server can be repeated within it's parent (domain)
class managed_server(RepeatableConfigItem):
    def __init__(self, name, host, port):
        super(managed_server, self).__init__(mc_key=name)
        self.name = name
        self.host = host
        self.port = port
        self.server_type = 'managed'
        self.another_prop = None


# Here we specify that a parameter num_servers is required when defining a
# builder for managed_server
@required('num_servers')
class managed_servers(ConfigBuilder):
    ''' Builder for managed_server objects. Used in environment configuration to
    automatically create proper number of managed_server objects '''
    def __init__(self, num_servers, host_pattern, base_port):
        super(managed_servers, self).__init__()
        self.num_servers = num_servers
        self.host_pattern = host_pattern
        self.base_port = base_port

    def build(self):
        for server_num in range(1, self.num_servers+1):
            # Here we are generating the managed_server's name and host name, from a pattern and the managed server number
            server_name = 'ms%d' % server_num
            host_name = self.host_pattern % dict(n=server_num)
            managed_server(name=server_name, host=host_name, port=self.base_port+10+server_num)


class datasource(RepeatableConfigItem):
    def __init__(self, name, database_type):
        super(datasource, self).__init__(mc_key=name)
        self.name = name
        self.database_type = database_type
