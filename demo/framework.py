# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from multiconf.decorators import nested_repeatables


# Here we define what can be repeated within the configuration item. In this case
# we will have many managed servers and datasources
@nested_repeatables('managed_servers', 'datasources')
class weblogic_config(ConfigItem):
    """This is just a simple holder of managed_servers and datasources."""
    def __init__(self):
        super().__init__()
        self.base_port = MC_REQUIRED


# Weblogic's standalone administration server. Used to control domain.
class admin_server(ConfigItem):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.name = 'admin'
        self.server_type = 'admin'


# Here specify that a managed_server can be repeated within it's parent (domain)
class managed_server(RepeatableConfigItem):
    def __init__(self, mc_key, host, port):
        super().__init__(mc_key=mc_key)
        self.host = host
        self.port = port
        self.name = mc_key
        self.server_type = 'managed'
        self.another_prop = None


class managed_servers(ConfigBuilder):
    """Builder for managed_server objects.

    Used in environment configuration to automatically create proper number of managed_server objects.
    """

    def __init__(self, num_servers, host_pattern, base_port):
        super().__init__()
        self.num_servers = num_servers
        self.host_pattern = host_pattern
        self.base_port = base_port

    def mc_build(self):
        for server_num in range(1, self.num_servers+1):
            # Here we are generating the managed_server's name and host name, from a pattern and the managed server number
            server_name = 'ms%d' % server_num
            host_name = self.host_pattern % dict(n=server_num)
            managed_server(server_name, host=host_name, port=self.base_port+10+server_num)


class datasource(RepeatableConfigItem):
    def __init__(self, mc_key, database_type):
        super().__init__(mc_key=mc_key)
        self.name = mc_key
        self.database_type = database_type
