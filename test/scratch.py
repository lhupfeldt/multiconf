#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

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

    def mc_init(self):
        self.setattr("aa", default=17, prod=self.aa)

with ConfigRoot(prod, [prod, pp]):
    with X() as x:
        x.setattr('aa', default=7, pp=17, prod=4)

print x.aa
