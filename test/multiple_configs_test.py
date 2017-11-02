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


def test_multiple_configs_same_env_factory():
    # Check that getting a config for another env does not change other configs current env

    @mc_config(ef)
    def config1(_):
        with ItemWithAABB() as ci:
            ci.setattr('aa', default=1, prod=2)

    @mc_config(ef)
    def config2(_):
        with ItemWithAABB() as ci:
            ci.setattr('aa', default=1, prod=3)

    cr1 = config1(prod)
    assert cr1.ItemWithAABB.aa == 2

    cr2 = config2(pp)
    assert cr2.ItemWithAABB.aa == 1
    assert cr1.ItemWithAABB.aa == 2

    cr2 = config2(prod)
    assert cr2.ItemWithAABB.aa == 3
    assert cr1.ItemWithAABB.aa == 2

    cr1 = config1(pp)
    assert cr1.ItemWithAABB.aa == 1
    assert cr2.ItemWithAABB.aa == 3
