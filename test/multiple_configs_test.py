# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

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

    @mc_config(ef, load_now=True)
    def config1(_):
        with ItemWithAABB() as ci:
            ci.setattr('aa', default=1, prod=2)

    @mc_config(ef, load_now=True)
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


def test_multiple_configs_different_env_factory():
    # Check that getting a config for another env does not change other configs current env

    ef2 = EnvFactory()
    ef2.Env('dev1')
    pp2 = ef2.Env('pp')
    prod2 = ef2.Env('prod')

    def aa():
        @mc_config(ef, load_now=True)
        def config(_):
            with ItemWithAABB() as ci:
                ci.setattr('aa', default=1, prod=2)
        return config

    def bb():
        @mc_config(ef2)
        def config(_):
            with ItemWithAABB() as ci:
                ci.setattr('aa', default=1, prod=3)
        return config

    cr1 = aa()(prod)
    assert cr1.ItemWithAABB.aa == 2

    cfg = bb()
    cfg.load()
    cr2 = cfg(pp2)
    assert cr2.ItemWithAABB.aa == 1
    assert cr1.ItemWithAABB.aa == 2

    cr2 = cfg(prod2)
    assert cr2.ItemWithAABB.aa == 3
    assert cr1.ItemWithAABB.aa == 2

    cr1 = aa()(pp)
    assert cr1.ItemWithAABB.aa == 1
    assert cr2.ItemWithAABB.aa == 3
