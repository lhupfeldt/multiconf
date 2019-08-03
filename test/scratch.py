#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.insert(0, jp(here, '..'))

from multiconf import mc_config, ConfigItem, ConfigException, ConfigDefinitionException, MC_REQUIRED, RepeatableConfigItem, ConfigBuilder
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory
from test.utils.utils import line_num
from test.utils.check_containment import check_containment


ef = EnvFactory()
prod = ef.Env('prod')
pp = ef.Env('pp')

class ItemWithAA(ConfigItem):
    def __init__(self):
        self.aa = None

@mc_config(ef, load_now=True)
def config(_):
    with ItemWithAA() as cr:
        print("here1")
        cr.setattr('aa', default=None, prod=1, pp=2)
        print("here2")

    print("here3")
print("here4")
cr = config(prod).ItemWithAA
assert cr.aa == 1
