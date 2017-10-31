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
            super(builder, self).__init__()
            self.y = 1

        def mc_validate(self):
            self.y = 7

        def mc_build(self):
            ItemWithAA(self)

    @mc_config(ef_pprd_prod)
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
        @mc_config(ef_pprd_prod)
        def config(_):
            with ConfigItem():
                builder()

    assert str(exinfo.value) == "Error in builder validate"
