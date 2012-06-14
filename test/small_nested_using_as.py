#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, ConfigItem
from ..envs import Env
from ..decorators import nested_repeatables, repeat

prod = Env('prod')
dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')

valid_envs = [dev2ct, dev2st, prod]

@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass

@repeat()
class RepeatableItem(ConfigItem):
    pass

def config(env):
    """Test config"""
    with project(env, valid_envs) as conf:

        with RepeatableItem(id=0, b='hello') as c:
            hello = "Hello"
            c.id(prod=3)
            c.a(prod=hello, dev2CT="hi", dev2ST="hay")
            with ConfigItem(c=1) as c:
                c.c(prod=2)

        with RepeatableItem(id=1, d='hello') as c:
            hello = "World"
            c.a(prod=hello, dev2CT="hi", dev2ST="hay")
            with ConfigItem(e=1) as c:
                c.e(prod=7)

        return conf

def test(env):
    """Create config and print some values"""
    conf = config(env)

    print "----", env, "----"
    print conf.RepeatableItems[0].a
    print conf.RepeatableItems[0].ConfigItem.c
    print conf.RepeatableItems[1].a
    print conf.RepeatableItems[1].ConfigItem.e
    print

    print "Full config:\n", conf

test(prod)
test(dev2ct)
