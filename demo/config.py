# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from framework import weblogic_config, admin_server, managed_server, managed_servers, datasource
from valid_envs import g_dev, prod

# This function is used to describe all environments and return environment
# configuration for environment *env*, which is passed as parameter
def conf(env):
    # this will define weblogic configuration for environment group "g_dev" and
    # for single environment "prod".
    # Take a look at valid_envs.py to see how environments are defined.
    # weblogic_config object is defined in framework.py
    with weblogic_config(env, [g_dev, prod]) as dc:
        # Here we will set domain base port number for different
        # environments
        dc.base_port(prod=7000, devi=7100, devs=7200)

        # weblogic will have admin server, which will be listening on
        # environment's base port plus one
        with admin_server(port=dc.base_port.value()+1) as c:
            # But admin server will be listening on different hosts
            c.host(prod='admin.prod.mydomain', devi='admin.devi.mydomain', devs='admin.devs.mydomain')

        # Here we define hom many managed servers we need in each environment:
        # prod will have four and all dev environments will have only one
        with managed_servers(num_servers=1) as c:
            c.num_servers(prod=4)

        # Add a special managed server, and add a property
        port = dc.base_port.value() + 110
        with managed_server(host='ms.'+env.name+'.mydomain', port=port+1, suffix=17) as c:
            # We will have that property set to one in prod and two in dev
            c.someprop(prod=1, g_dev=2)

        # Add a special managed server, and override default value
        port = dc.base_port.value() + 210
        with managed_server(host='ms.'+env.name+'.mydomain', port=port+1, suffix=17, another_prop=[1]) as c:
            c.another_prop(prod=[1, 2])

        # Add a managed server with no explicit env specific properties
        managed_server(host='ms.'+env.name+'.mydomain', port=port+2, suffix=18)

        with datasource(xx=18) as c:
            c.xx(prod=19)

        with datasource(xx=16) as c:
            c.xx(prod=17)

        # Returned weblogic config will have settings only for environment
        # passed as argument for this function
        return dc
