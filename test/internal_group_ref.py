#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, ConfigItem
from ..envs import Env, EnvGroup
from ..decorators import nested_repeatables, named_as, repeat

prod = Env('prod')
dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
g_dev = EnvGroup('g_dev', dev2st, dev2ct)

valid_envs = [g_dev, prod]

@nested_repeatables('someitems')
class project(ConfigRoot):
    pass

@named_as('someitems')
@repeat()
class RepeatableItem(ConfigItem):
    pass

def conf(env):
    with project(env, valid_envs) as dc:
        dc.ms_suffixes(prod=[1, 2, 3, 4], g_dev=[1])
        print dc.ms_suffixes

        for ms_suffix in dc.ms_suffixes.value():
            with RepeatableItem(id=ms_suffix-1, suffix=ms_suffix) as c:
                assert c.suffix().value() == ms_suffix

        return dc


def test(env, exp_ms_suffixes, exp_suffix):
    print '---- Loading Config: ' + repr(env) + ' -----'
    c = conf(env)
    print '---- Loaded -----'
    print '---- Printing -----'
    print 'c.ms_suffixes:', repr(c.ms_suffixes)
    assert c.ms_suffixes == exp_ms_suffixes
    print 'c.someitems:', repr(c.someitems)
    print 'c.someitems[0]:', repr(c.someitems[0])
    print 'c.someitems[0].suffix:', repr(c.someitems[0].suffix)
    assert c.someitems[0].suffix == exp_suffix
    print '---- Printed -----'

test(prod, [1, 2, 3, 4], 1)
print
test(dev2ct, [1], 1)
