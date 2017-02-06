#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

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


@named_as('r')
class RepeatableChild(RepeatableConfigItem):
    pass

class UnexpectedRepeatableChildBuilder(ConfigBuilder):
    def mc_build(self):
        RepeatableChild(mc_key=None)

@mc_config(ef)
def _(_):
    with ConfigItem():
        UnexpectedRepeatableChildBuilder()
