# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem
from multiconf.envs import EnvFactory


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)

ef3_dev1_pp_prod = EnvFactory()
dev13 = ef3_dev1_pp_prod.Env('dev1')
pp3 = ef3_dev1_pp_prod.Env('pp')
prod3 = ef3_dev1_pp_prod.Env('prod')
ef3_dev1_pp_prod.EnvGroup('g_prod_like', prod3, pp3, dev13)

ef4_a_dev1_pp_prod = EnvFactory()
_a = ef4_a_dev1_pp_prod.Env('a')
dev14 = ef4_a_dev1_pp_prod.Env('dev1')
pp4 = ef4_a_dev1_pp_prod.Env('pp')
prod4 = ef4_a_dev1_pp_prod.Env('prod')
ef4_a_dev1_pp_prod.EnvGroup('g_prod_like', _a, prod4, pp4)

ef5_a_dev1_pp_prod = EnvFactory()
_a = ef5_a_dev1_pp_prod.Env('a')
dev15 = ef5_a_dev1_pp_prod.Env('dev1')
pp5 = ef5_a_dev1_pp_prod.Env('pp')
prod15 = ef5_a_dev1_pp_prod.Env('prod1')
prod25 = ef5_a_dev1_pp_prod.Env('prod2')
g_prod5 = ef5_a_dev1_pp_prod.EnvGroup('g_prod', _a, prod15, prod25)
ef5_a_dev1_pp_prod.EnvGroup('g_prod_like', _a, g_prod5, pp5)


def test_contained_in_root_conf():
    @mc_config(ef2_pp_prod, load_now=True)
    def config(root):
        with ConfigItem() as conf:
            assert conf.root_conf == root
            assert conf.root_conf.ConfigItem == conf
            assert conf.contained_in == conf.root_conf
            assert conf.contained_in.contained_in is None

            with ConfigItem() as c1:
                assert c1.root_conf == root
                assert c1.contained_in == conf

                with ConfigItem() as c2:
                    assert c2.root_conf == root
                    assert c2.contained_in == c1

        return c1, c2

    conf = config(prod2)
    c1, c2 = conf.mc_config_result

    assert conf.contained_in is None
    # assert c1.root_conf == conf
    # assert c1.contained_in == conf
    # assert c2.root_conf == conf
    assert c2.contained_in == c1
