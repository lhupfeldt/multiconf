# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from framework import weblogic_config, admin_server, managed_server, managed_servers, datasource
from valid_envs import g_dev, prod

def conf(env):
    with weblogic_config(env, [g_dev, prod]) as dc:
        dc.base_port(prod=7000, devi=7100, devs=7200)

        dc.ms_suffixes(prod=[1, 2, 3, 4], g_dev=[1])

        with admin_server(port=dc.base_port.value()+1) as c:
            c.host(prod='admin.prod.xleap', devi='admin.dev2ct.xleap', devs='admin.dev2st.xleap')

        with managed_servers(num_servers=4) as c:
            c.num_servers(g_dev=1)
            
        # Add a special managed server, and add a property
        port = dc.base_port.value() + 110        
        with managed_server(host='ms.'+env.name+'.xleap', port=port+1, suffix=17) as c:
            c.someprop(prod=1, g_dev=2)

        # Add a special managed server, and override default value
        port = dc.base_port.value() + 210
        with managed_server(host='ms.'+env.name+'.xleap', port=port+1, suffix=17, another_prop=[1]) as c:
            c.another_prop(prod=[1, 2])

        # Add a managed server with no explicit env specific properties
        managed_server(host='ms.'+env.name+'.xleap', port=port+2, suffix=18)
            
        with datasource(xx=18) as c:
            c.xx(prod=19)

        with datasource(xx=16) as c:
            c.xx(prod=17)

        return dc
