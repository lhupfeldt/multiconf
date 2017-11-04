# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from multiconf import mc_config, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAABB


ef = EnvFactory()
dev1 = ef.Env('dev1')
pp = ef.Env('pp')
prod = ef.Env('prod')


def test_lazy_load():
    @mc_config(ef, lazy_load=True)
    def config(_):
        with ItemWithAABB() as ci:
            ci.setattr('aa', default=1, prod=2)

    cr1 = config(prod)
    assert cr1.ItemWithAABB.aa == 2
