# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem
from multiconf.envs import EnvFactory

ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


def test_mc_init_ref_env_attr_and_override():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super().__init__()
            self.aa = aa

        def mc_init(self):
            self.setattr('aa', default=self.aa + 1, mc_force=True)

    class Y(X):
        def __init__(self, aa=37):
            super().__init__()
            self.aa = aa
            self.bb = 1
            self.cc = None

        def mc_init(self):
            super().mc_init()
            self.setattr('aa', default=self.aa + 1, mc_force=True)
            self.setattr('bb', default=self.bb + 1, mc_force=True)
            self.setattr('cc', default=17, mc_force=True)

    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem():
            X()
            Y()

    cr = config(prod).ConfigItem
    assert cr.X.aa == 2
    assert cr.Y.aa == 39

    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem():
            with X(aa=2) as x:
                x.aa = 3

    cr = config(pp).ConfigItem
    assert cr.X.aa == 4

    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem():
            with X(aa=2) as x:
                x.setattr('aa', default=3, pp=5)

    cr = config(pp).ConfigItem
    assert cr.X.aa == 6

    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem():
            with Y(aa=2) as y:
                y.aa = 3

    cr = config(pp).ConfigItem
    assert cr.Y.aa == 5
    assert cr.Y.bb == 2
    assert cr.Y.cc == 17
