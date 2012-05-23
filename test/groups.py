#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from .. import ConfigRoot, ConfigItem
from ..envs import Env, EnvGroup
from ..decorators import nested_repeatables, named_as, repeat

prod = Env('prod')
dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
g_dev = EnvGroup('g_dev', dev2st, dev2ct)

valid_envs = [g_dev, prod]

@nested_repeatables('ritems')
class project(ConfigRoot):
    pass

@named_as('ritems')
@repeat()
class RepeatableItem(ConfigItem):
    pass

def config(env):
    with project(env, valid_envs) as conf:
        conf.a(prod="hello", g_dev="hi")
        print 'conf.a:', conf.a

        with RepeatableItem(id=0) as c:
            c.a(prod="hello nested", g_dev="hi nested")

        return conf

def test(env):
    conf = config(env)

    print "----", env, "----"
    print 'conf.a', repr(conf.a)
    print 'conf.ritems[0].a', repr(conf.ritems[0].a)
    print

    print "Full config:\n", conf

test(prod)
test(dev2ct)
