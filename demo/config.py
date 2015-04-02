# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from framework import weblogic_config, admin_server, managed_server, managed_servers, datasource
from multiconf.envs import EnvFactory

# Define environments

# Use EnvFactory() to create environment or group of environments
ef = EnvFactory()

# We have five environments and we define them here
devlocal = ef.Env('devlocal')
devi = ef.Env('devi')
devs = ef.Env('devs')
preprod = ef.Env('preprod')
prod = ef.Env('prod')

# Grouping environments per their roles
g_dev = ef.EnvGroup('g_dev', devlocal, devi, devs)
g_prod = ef.EnvGroup('g_prod', preprod, prod)


# This function is used to describe all environments and return an instantiated environment
# configuration for environment with name 'env_name', which is passed as parameter
def conf(env_name):
    env = ef.env(env_name)

    # This will define a weblogic configuration for all environments defined above
    # But the result of execution of conf() will be the setting for environment
    # passed as argument 'env_name'
    # Use EnvFactory 'ef' to define the required/allowed environments
    # The 'weblogic_config' class is defined in framework.py
    with weblogic_config(env, ef) as dc:
        # Set domain base port number for different environments.
        # Domain base port is used as base to calculate port offsets
        # Here we're saying that Weblogic in g_prod group will have
        # attribute base_port set to 7000, and each of the development environments
        # will have unique base_port
        dc.setattr('base_port', g_prod=7000, devi=7100, devs=7200, devlocal=7300)

        # Weblogic will have an admin server, which will be listening on the environment's base port plus one
        # But admin server will be running on different hosts, where the default value is calculated using the
        # environment name
        # In this example default host name will be 'admin.devlocal.mydomain' for 'devlocal' environment.
        # 'admin.devi.mydomain' for 'devi' environment and so on for all advironments
        with admin_server(host='admin.'+env.name+'.mydomain', port=dc.base_port+1) as adm_server:
            # But on 'devs' environment we can't use that host name - we are overriding defaults here
            # same applies to 'devlocal' environment
            adm_server.setattr('host', devs='admin.special.otherdomain', devlocal='localhost')

        # Here we define how many managed servers we need in each environment, the default is set to 4:
        # It is considered good practice to always have the prod value as default, you don't want somebody
        # to forget overriding a property with the correct prod value
        with managed_servers(num_servers=4, host_pattern='ms%(n)d.'+env.name+'.mydomain', base_port=dc.base_port) as ms:
            # But dev envs will only have 1 managed server
            # This override uses group 'g_dev', which has all development environments
            ms.setattr('num_servers', g_dev=1)
            # Same as above - we cannot use default host naming in two environments
            ms.setattr('host_pattern', devs='ms.special.otherdomain', devlocal='localhost')

        # Add some special managed servers, with custom properties

        # Here we are getting the domain base port value set above
        port = dc.base_port + 110
        # And we are using this variable to pass as 'port' parameter
        with managed_server(name='ms5', host='ms.'+env.name+'.mydomain', port=port+1) as ms:
            # Same as above - we cannot use default host naming in two environments
            ms.setattr('host', devs='ms.special.otherdomain', devlocal='localhost')
            # This server needs to have custom property, which is set to different values
            # in different environment groups
            # We will have that property set to one in prod and preprod and two in all dev environments
            ms.setattr('custom_property', g_prod=1, g_dev=2)

        # Add a special managed server, and override default value
        port = dc.base_port + 210
        # Managed server 'ms6' have property 'another_prop', which is set to default value [1, 2]
        with managed_server(name='ms6', host='ms.'+env.name+'.mydomain', port=port+1) as ms:
            # But on 'g_dev' group it needs to be set to another value
            ms.setattr('another_prop', default=[1, 2], g_dev=[1])
            # Same as above - we cannot use default host naming in two environments
            ms.setattr('host', devs='ms.special.otherdomain', devlocal='localhost')

        # Add a managed server with no explicit env specific properties
        # This means all environment will have the same settings for this
        # server
        # Except 'host' parameter, which is different for two environments
        with managed_server(name='ms7', host='ms.'+env.name+'.mydomain', port=port+2) as ms:
            # Same as above - we cannot use default host naming in two environments
            ms.setattr('host', devs='ms.special.otherdomain', devlocal='localhost')

        # Here we define data source used by this domain
        with datasource(name='SampleDS_one', database_type="OracleRAC") as c:
            # but in dev envs we are not using RAC
            c.setattr('database_type', g_dev="Oracle")

        # This datasource is the same for all environments
        datasource(name='SampleDS_two', database_type="SQLServer")

        # Returned weblogic config will have settings only for environment
        # passed as argument for this function
        return dc

# So after we execute conf('devlocal') we have this as the result:
#
# Weblogic domain with base_port = 7300
#   Admin server on host 'localhost' and on port = 7301
#   Managed servers:
#       'ms1', on host 'localhost' and on port 7310 (naming of servers and port numbering
#           will be defined within managed_server class from framework.py)
#       'ms5', on host 'localhost' and on port 7411, with custom_property=2 (defaults overridden on lines 67-73)
#       'ms6', on host 'localhost' and on port 7511, with another_prop=[1] (overridden on lines 78-82)
#       'ms7', on host 'localhost' and on port 7513
#   Datasource 'SampleDS_one' with database_type='Oracle'
#   Datasource 'SampleDS_two' with database_type='SQLServer'
#
# Here is what we would have if we execute conf('prod'):
#
# Weblogic domain with base_port = 7000
#   Admin server on host 'admin.prod.mydomain' and on port = 7001
#   Managed servers:
#       'ms1', on host 'ms1.prod.mydomain' and on port 7010 (naming of servers and port numbering
#           will be defined within managed_server class from framework.py)
#       'ms2', on host 'ms2.prod.mydomain' and on port 7010 (naming of servers and port numbering
#       'ms3', on host 'ms1.prod.mydomain' and on port 7020 (naming of servers and port numbering
#       'ms4', on host 'ms2.prod.mydomain' and on port 7020 (naming of servers and port numbering
#       'ms5', on host 'ms.prod.mydomain' and on port 7111, with custom_property=1 (defaults overridden on lines 67-73)
#       'ms6', on host 'ms.prod.mydomain' and on port 7211, with another_prop=[1, 2] (default on line 78)
#       'ms7', on host 'ms.prod.mydomain' and on port 7213
#   Datasource 'SampleDS_one' with database_type='OracleRAC'
#   Datasource 'SampleDS_two' with database_type='SQLServer'
#
# As you can see, all of this defined in one small file. Ports and host names are calculated automatically
# and match within environment. There is no need to maintain multiple property files per environment per
# multiple environments.
