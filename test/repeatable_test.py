# Copyright (c) 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys

from pytest import raises

from multiconf import mc_config, ConfigItem
from multiconf.decorators import nested_repeatables
from multiconf.envs import EnvFactory


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class root(ConfigItem):
    pass


def test_manual_insert_in_repeatable_not_allowed():
    with raises(TypeError):
        @mc_config(ef)
        def config(_):
            with root() as cr:
                cr.children['hello'] = 1
