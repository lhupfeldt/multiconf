# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from framework import weblogic_config, admin_server, managed_server, managed_servers, datasource
from valid_envs import ef, g_dev, prod

# This function is used to describe all environments and return environment
# configuration for environment with name 'env_name', which is passed as parameter
def conf(env_name):
    env = ef.env(env_name)

    # This will define weblogic configuration for environment group "g_dev" and for single environment "prod".
    # Take a look at valid_envs.py to see how environments are defined.
    # weblogic_config object is defined in framework.py
    with weblogic_config(env, [g_dev, prod]) as dc:
        # Here we will set domain base port number for different
        # environments. Domain base port is used as base to calculate port
        # offsets
        dc.base_port(prod=7000, devi=7100, devs=7200)
        dc.freeze()

        # weblogic will have admin server, which will be listening on
        # environment's base port plus one
        with admin_server(port=dc.base_port+1) as c:
            # But admin server will be listening on different hosts
            c.host(prod='admin.prod.mydomain', devi='admin.devi.mydomain', devs='admin.devs.mydomain')

        # Here we define hom many managed servers we need in each environment:
        # by default only one managed server in environment
        with managed_servers(num_servers=1) as c:
            # But prod will have 4
            c.num_servers(prod=4)

        # Add a special managed server, and add custom roperty

        # here we getting domain base port value set above
        port = dc.base_port + 110
        with managed_server(host='ms.'+env.name+'.mydomain', port=port+1, suffix=17) as c:
            # We will have that property set to one in prod and two in dev
            c.custom_property(prod=1, g_dev=2)

        # Add a special managed server, and override default value
        port = dc.base_port + 210
        with managed_server(host='ms.'+env.name+'.mydomain', port=port+1, suffix=17, another_prop=[1]) as c:
            c.another_prop(prod=[1, 2])

        # Add a managed server with no explicit env specific properties
        # This means all environment will have the same settings for this
        # server
        managed_server(host='ms.'+env.name+'.mydomain', port=port+2, suffix=18)

        # Here we define data source used by this domain
        with datasource(name='SampleDS_one', database_type="Oracle") as c:
            # and in prod we are going to use Oracle RAC
            c.database_type(prod="OracleRAC")

        # This datasource is the same for all environments
        datasource(name='SampleDS_two', database_type="SQLServer")

        # Returned weblogic config will have settings only for environment
        # passed as argument for this function
        return dc

