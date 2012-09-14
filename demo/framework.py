# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigRoot, ConfigItem, ConfigBuilder
from multiconf.decorators import nested_repeatables, repeat, required

# Here we define what can be repeated within configuration item. In this case
# we will have many managed servers and datasources
@nested_repeatables('managed_servers, datasources')
class weblogic_config(ConfigRoot):
    ''' This is just a simple holder of managed_servers and datasources '''
    def __init__(self, selected_env, valid_envs, **attr):
        super(weblogic_config, self).__init__(selected_env, valid_envs, **attr)


# Weblogic's standalone administration server. Used to control domain.
class admin_server(ConfigItem):
    def __init__(self, **attr):
        super(admin_server, self).__init__(server_type='admin', **attr)


# Here we saying that managed_server can be repeated within it's holder
@repeat()
class managed_server(ConfigItem):
    def __init__(self, **attr):
        super(managed_server, self).__init__(server_type='managed', **attr)


# Here we saying that parameter num_servers is required when we defining a
# builder for managed_server
@required('num_servers')
@repeat()
class managed_servers(ConfigBuilder):
    ''' Builder for managed_server objects. Used in environment configuration to
    automatically create proper number of managed_server objects '''
    def __init__(self, **attr):
        super(managed_servers, self).__init__(**attr)

    def build(self):
        for server_num in xrange(1, self.num_servers+1):
            # Here we generating managed_server's name
            with managed_server(name='ms%d' % server_num) as c:
                # call for override is required because we changed default
                # parameter
                self.override(c)


@repeat()
class datasource(ConfigItem):
    def __init__(self, **attr):
        super(datasource, self).__init__(**attr)


