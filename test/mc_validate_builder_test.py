# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigBuilder
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA


ef_pprd_prod = EnvFactory()
pprd = ef_pprd_prod.Env('pprd')
prod = ef_pprd_prod.Env('prod')


def test_builder_mc_validate_set_attribute():
    class builder(ConfigBuilder):
        def __init__(self):
            super().__init__()
            self.y = 1

        def mc_validate(self):
            self.y = 7

        def mc_build(self):
            ItemWithAA(self)

    @mc_config(ef_pprd_prod, load_now=True)
    def config(_):
        builder()

    cr = config(prod)
    assert cr.ItemWithAA.aa.y == 7


def test_user_mc_validate_error_builder():
    class builder(ConfigBuilder):
        def mc_build(self):
            pass

        def mc_validate(self):
            raise Exception("Error in builder validate")

    with raises(Exception) as exinfo:
        @mc_config(ef_pprd_prod, load_now=True)
        def config(_):
            with ConfigItem():
                builder()

    assert str(exinfo.value) == "Error in builder validate"


def test_builder_mc_validate_child_item_only_called_once_per_env():
    num_calls_builder = {pprd: 0, prod: 0}
    num_calls_built = {pprd: 0, prod: 0}
    num_calls_child = {pprd: 0, prod: 0}

    class Built(ItemWithAA):
        def mc_validate(self):
            num_calls_built[self.env] += 1

    class Child(ItemWithAA):
        def mc_validate(self):
            num_calls_child[self.env] += 1

    class builder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_validate(self):
            num_calls_builder[self.env] += 1

        def mc_build(self):
            Built(3)

    @mc_config(ef_pprd_prod, load_now=True)
    def config(_):
        with builder():
            Child(4)

    cr = config(prod)
    assert cr.Built.aa == 3
    assert cr.Built.Child.aa == 4
    assert num_calls_builder[prod] == 1
    assert num_calls_builder[pprd] == 1
    assert num_calls_built[prod] == 1
    assert num_calls_built[pprd] == 1
    assert num_calls_child[prod] == 1
    assert num_calls_child[pprd] == 1
