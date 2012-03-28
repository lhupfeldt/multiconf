# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from framework import weblogic_config, admin_server, managed_server, datasource
from valid_envs import g_dev, prod

def conf(env):
    with weblogic_config(env, [g_dev, prod]) as dc:
        dc.prod.base_port = 7000
        dc.devi.base_port = 7100
        dc.devs.base_port = 7200

        dc.prod.ms_suffixes = [1, 2, 3, 4]
        dc.g_dev.ms_suffixes = [1]

        with admin_server(port=dc.base_port+1) as c:
            c.prod.host = 'admin.prod.xleap'
            c.devi.host = 'admin.dev2ct.xleap'
            c.devs.host = 'admin.dev2st.xleap'

        for ms_suffix in dc.ms_suffixes:
            port = dc.base_port + 10 + ms_suffix
            with managed_server(port=port, suffix=ms_suffix) as c:
                c.prod.host = 'ms%d.prod.xleap' % c.suffix
                c.g_dev.host = 'ms%d.dev2.xleap' % c.suffix

        # Add a special managed server, and override group value
        with managed_server(host='ms.'+env.name+'.xleap', port=port+1, suffix=17) as c:
            c.prod.someprop = 1
            c.g_dev.someprop = 2
            c.devi.someprop = 3

        # Add a managed server with no explicit env specific properties
        managed_server(host='ms.'+env.name+'.xleap', port=port+2, suffix=18)
            
        with datasource(xx=18) as c:
            c.prod.xx = 19

        with datasource(xx=16) as c:
            c.prod.xx = 17

        return dc
