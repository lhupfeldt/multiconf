#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException, ConfigDefinitionException, MC_REQUIRED, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as, required, unchecked
from multiconf.envs import EnvFactory
from multiconf.test.utils.utils import lineno
from multiconf.test.utils.check_containment import check_containment


ef = EnvFactory()
prod = ef.Env('prod')


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


@nested_repeatables('someitems')
class root(ConfigRoot):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                 mc_allow_todo=False, mc_allow_current_env_todo=False):
        super(root, self).__init__(
            selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
            mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
        self.a = None
        self.q = None


with root(prod, ef) as cr:
    cr.a = 0
    cr.q = 17
    NestedRepeatable(id=1)
    with X() as ci:
        ci.setattr('a', prod=0)
        with NestedRepeatable(id='a') as nr:
            nr.a = 9
        with NestedRepeatable(id='b') as ci:
            with NestedRepeatable(id='c') as nr:
                nr.a = 7
            with X() as ci:
                ci.setattr('b?', prod=1)
                with NestedRepeatable(id='d') as ci:
                    ci.setattr('a', prod=2)
                    with X() as ci:
                        ci.setattr('a', prod=3)
        
