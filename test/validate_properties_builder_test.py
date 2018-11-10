# Copyright (c) 2018 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigBuilder
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA


ef_pprd_prod = EnvFactory()
pprd = ef_pprd_prod.Env('pprd')
prod = ef_pprd_prod.Env('prod')


def test_builder_validate_properties_child_item_only_called_once_per_env():
    num_calls_builder = {pprd: 0, prod: 0}
    num_calls_built = {pprd: 0, prod: 0}
    num_calls_child = {pprd: 0, prod: 0}

    class Built(ItemWithAA):
        @property
        def mm(self):
            num_calls_built[self.env] += 1
            return 14

    class Child(ItemWithAA):
        @property
        def mm(self):
            num_calls_child[self.env] += 1
            return 15

    class builder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        @property
        def mm(self):
            num_calls_builder[self.env] += 1
            return 16

        def mc_build(self):
            Built(3)

    @mc_config(ef_pprd_prod, load_now=True)
    def config(_):
        with builder():
            Child(4)

    cr = config(prod)
    assert cr.num_invalid_property_usage == 0
    assert cr.Built.aa == 3
    assert cr.Built.Child.aa == 4

    assert num_calls_builder[prod] == 1
    assert num_calls_builder[pprd] == 1
    assert num_calls_built[prod] == 1
    assert num_calls_built[pprd] == 1
    assert num_calls_child[prod] == 1
    assert num_calls_child[pprd] == 1

    assert cr.Built.mm == 14
    assert cr.Built.Child.mm == 15
