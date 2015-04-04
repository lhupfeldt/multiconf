# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import ConfigRoot, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children_mc_init')
class root(ConfigRoot):
    pass


@named_as('children_mc_init')
class rchild_mc_init(RepeatableConfigItem):
    def __init__(self):
        super(rchild_mc_init, self).__init__()
        self.xx = None

    def mc_init(self):
        super(rchild_mc_init, self).__init__()
        self.override('xx', 17)
        self.override('yy', 17)


def test_mc_init_ref_env_attr_and_override():
    class X(ConfigItem):
        def __init__(self, aa=1):
            super(X, self).__init__()
            self.aa = aa

        def mc_init(self):
            self.override('aa', self.aa + 1)

    class Y(X):
        def __init__(self, aa=37):
            super(Y, self).__init__()
            self.aa = aa
            self.bb = 1
            self.cc = None

        def mc_init(self):
            super(Y, self).mc_init()
            self.override('aa', self.aa + 1)
            self.override('bb', self.bb + 1)
            self.override('cc', 17)

    with ConfigRoot(prod, ef) as cr:
        X()
        Y()
    assert cr.X.aa == 2
    assert cr.Y.aa == 39

    with ConfigRoot(pp, ef) as cr:
        with X(aa=2) as x:
            x.aa = 3
    assert cr.X.aa == 4

    with ConfigRoot(pp, ef) as cr:
        with X(aa=2) as x:
            x.setattr('aa', default=3, pp=5)
    assert cr.X.aa == 6

    with ConfigRoot(pp, ef) as cr:
        with Y(aa=2) as y:
            y.aa = 3
    assert cr.Y.aa == 5
    assert cr.Y.bb == 2
    assert cr.Y.cc == 17
