# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from framework import weblogic_config, admin_server, managed_server, datasource
from valid_envs import g_dev, prod

def conf(env):
    with weblogic_config(env, [g_dev, prod]) as dc:
        dc.base_port(prod=7000, devi=7100, devs=7200)

        dc.ms_suffixes(prod=[1, 2, 3, 4], g_dev=[1])

        with admin_server(port=dc.base_port.value()+1) as c:
            c.host(prod='admin.prod.xleap', devi='admin.dev2ct.xleap', devs='admin.dev2st.xleap')

        for ms_suffix in dc.ms_suffixes.value():
            port = dc.base_port.value() + 10 + ms_suffix
            with managed_server(port=port, suffix=ms_suffix) as c:
                c.host(prod='ms%d.prod.xleap' % ms_suffix, g_dev='ms%d.dev2.xleap' % ms_suffix)

        # Add a special managed server, and override group value
        with managed_server(host='ms.'+env.name+'.xleap', port=port+1, suffix=17) as c:
            c.someprop(prod=1, g_dev=2)

        # Add a managed server with no explicit env specific properties
        managed_server(host='ms.'+env.name+'.xleap', port=port+2, suffix=18)
            
        with datasource(xx=18) as c:
            c.xx(prod=19)

        with datasource(xx=16) as c:
            c.xx(prod=17)

        return dc
