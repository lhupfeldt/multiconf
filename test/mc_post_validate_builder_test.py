# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigBuilder
from multiconf.envs import EnvFactory


ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)


def test_call_of_mc_post_validate_builder():
    ii = []

    class builder(ConfigBuilder):
        y = 7

        def __init__(self):
            self.aa = None

        def mc_post_validate(self):
            assert self.y == 7
            assert self.getattr('aa', pp2) < self.getattr('aa', prod2)

        def mc_build(self):
            pass

    @mc_config(ef2_pp_prod)
    def config(_):
        with builder() as bb:
            bb.setattr('aa', pp=1, prod=2)
        ii.append(bb)

    cr = config(prod2)
    assert ii[0].y == 7


def test_builder_user_mc_post_validate_error():
    class builder(ConfigBuilder):
        def mc_build(self):
            pass

        def mc_post_validate(self):
            raise Exception("Error in builder mc_post_validate")

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def config(_):
            builder()

    assert str(exinfo.value) == "Error in builder mc_post_validate"
