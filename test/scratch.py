#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException, ConfigDefinitionException, MC_REQUIRED
from multiconf.decorators import nested_repeatables, repeat, required_if, named_as, required, unchecked
from multiconf.envs import EnvFactory
from multiconf.test.utils.utils import lineno
from multiconf.test.utils.check_containment import check_containment


ef = EnvFactory()

dev2ct = ef.Env('dev2ct')
dev2st = ef.Env('dev2st')
g_dev = ef.EnvGroup('g_dev', dev2ct, dev2st)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)


@named_as('someitem')
class Nested(ConfigItem):
    @property
    def other_conf_item(self):
        self.json()


class X(ConfigItem):
    def __init__(self, aa=1):
        super(X, self).__init__()
        self.aa = aa


@named_as('anitem')
class AnXItem(ConfigItem):
    pass

with ConfigRoot(prod, ef, a=0) as cr:
    print("cr id:", id(cr))
    with X(aa='b2') as ref_x:
        print("ref_x id:", id(ref_x))
        ref_x.setattr('a', default=1, pp=2)
    with AnXItem(something=3) as last_item:
        print("last_item id:", id(last_item))
        last_item.setattr('ref', default=ref_x, prod=ref_x)

print(cr)
