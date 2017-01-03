#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.insert(0, jp(here, '..'))

from multiconf import mc_config, ConfigItem, ConfigException, ConfigDefinitionException, MC_REQUIRED, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory
from test.utils.utils import line_num
from test.utils.check_containment import check_containment


ef = EnvFactory()
prod = ef.Env('prod')
pp = ef.Env('pp')


@named_as('someitems')
@nested_repeatables('someitems')
class NestedRepeatable(RepeatableConfigItem):
    def __init__(self, id):
        super(NestedRepeatable, self).__init__(mc_key=id)
        self.id = id
        self.a = None


@named_as('x')
@nested_repeatables('someitems')
class X(ConfigItem):
    def __init__(self):
        super(X, self).__init__()
        self.a = MC_REQUIRED



@named_as('someitem')
class Nested(ConfigItem):
    @property
    def m(self):
        raise Exception("bad property method")


@mc_config(ef)
def _(_):
    with Nested() as nn:
        nn.setattr('m', prod=7, mc_overwrite_property=True)

cr = ef.config(prod)
assert cr.someitem.m == 7

@mc_config(ef)
def _(_):
    with Nested() as nn:
        nn.setattr('m', pp=7, mc_overwrite_property=True)

cr = ef.config(prod)
print(cr.someitem.m)
