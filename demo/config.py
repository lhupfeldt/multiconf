# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from framework import weblogic_config, admin_server, managed_server, managed_servers, datasource
from multiconf.envs import EnvFactory

# Define environments

# Use EnvFactory() to create environment or group of environments
ef = EnvFactory()

devlocal = ef.Env('devlocal')
devi = ef.Env('devi')
devs = ef.Env('devs')
preprod = ef.Env('preprod')
prod = ef.Env('prod')

# Define groups of environments
g_dev = ef.EnvGroup('g_dev', devlocal, devi, devs)
g_prod = ef.EnvGroup('g_prod', preprod, prod)


# This function is used to describe all environments and return an instantiated environment
# configuration for environment with name 'env_name', which is passed as parameter
def conf(env_name):
    env = ef.env(env_name)

    # This will define a weblogic configuration for environment all environments defined aboved
    # Use the goups "g_dev" and "g_prod" to define the required/allowed environments
    # The 'weblogic_config' class is defined in framework.py
    with weblogic_config(env, [g_dev, g_prod]) as dc:
        # Set domain base port number for different environments.
        # Domain base port is used as base to calculate port offsets
        dc.setattr('base_port', g_prod=7000, devi=7100, devs=7200, devlocal=7300)

        # Weblogic will have an admin server, which will be listening on the environment's base port plus one
        # But admin server will be running on different hosts, where the default value is calculated using the 
        # environment name
        with admin_server(host='admin.'+env.name+'.mydomain', port=dc.base_port+1) as adm_server:
            adm_server.setattr('host', devs='admin.devs.mydomain', devlocal='localhost')

        # Here we define hom many managed servers we need in each environment, the default is set to 4:
        # It is considered good practice to always have the prod value as default, you don't want somebody
        # to forget overriding a property with the correct prod value
        with managed_servers(num_servers=4, base_port=dc.base_port) as c:
            # But dev envs will only have 1
            c.setattr('num_servers', g_dev=1)

        # Add a special managed server, and add custom property

        # Here we are getting the domain base port value set above
        port = dc.base_port + 110
        with managed_server(host='ms.'+env.name+'.mydomain', port=port+1, suffix=17) as ms:
            ms.setattr('host', devlocal='localhost')
            # We will have that property set to one in prod and preprod and two in all dev environments
            ms.setattr('custom_property', g_prod=1, g_dev=2)

        # Add a special managed server, and override default value
        port = dc.base_port + 210
        with managed_server(host='ms.'+env.name+'.mydomain', port=port+1, suffix=17, another_prop=[1, 2]) as c:
            c.setattr('another_prop', g_dev=[1])

        # Add a managed server with no explicit env specific properties
        # This means all environment will have the same settings for this
        # server
        managed_server(host='ms.'+env.name+'.mydomain', port=port+2, suffix=18)

        # Here we define data source used by this domain
        with datasource(name='SampleDS_one', database_type="OracleRAC") as c:
            # but in dev envs we are not using RAC
            c.setattr('database_type', g_dev="Oracle")

        # This datasource is the same for all environments
        datasource(name='SampleDS_two', database_type="SQLServer")

        # Returned weblogic config will have settings only for environment
        # passed as argument for this function
        return dc

