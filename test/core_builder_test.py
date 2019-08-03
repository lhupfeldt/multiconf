# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigBuilder
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA


ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)


def test_builder_ref_env_attr_and_override():
    class X(ItemWithAA):
        def mc_init(self):
            self.setattr('aa', default=self.aa + 1, mc_force=True)

    class XBuilder(ConfigBuilder):
        def __init__(self, aa=17):
            super().__init__()
            self.aa = aa

        def mc_init(self):
            self.setattr('aa', default=self.aa - 1, mc_force=True)

        def mc_build(self):
            # Note: In pre v6 every attribute set in builder would be set on parent! This is no longer the case
            self.setattr('aa', default=self.aa + 3, mc_force=True)
            X(1)

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        XBuilder()

    cr = config(prod2)
    assert not hasattr(cr, 'aa')  # Note: in pre v6 cr.aa == 19
    assert cr.X.aa == 2  # Note: in pre v6 cr.X.aa == 16

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with XBuilder(aa=2) as x:
            x.aa = 3

    cr = config(pp2)
    assert not hasattr(cr, 'aa')  # Note: in pre v6 cr.aa == 5
    assert cr.X.aa == 2

    @mc_config(ef2_pp_prod, load_now=True)
    def config(_):
        with XBuilder(aa=2) as x:
            x.setattr('aa', default=3, pp=5)

    cr = config(pp2)
    assert not hasattr(cr, 'aa')  # Note: in pre v6 cr.aa == 7
    assert cr.X.aa == 2  # Note: in pre v6 cr.X.aa == 4
