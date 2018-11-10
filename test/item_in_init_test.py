# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem
from multiconf.envs import EnvFactory

ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


def test_item_in_init_goes_to_parent():
    parent = [None]

    class X(ConfigItem):
        def __init__(self, aa=1):
            super().__init__()
            self.aa = aa

    class Y(X):
        def __init__(self, aa=37):
            parent[0] = self.contained_in
            bb = X()  # X is created in parent and ref assigned to bb
            super().__init__(aa)
            self.bb = bb
            self.cc = None

    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem():
            with ConfigItem():
                Y()

    it = config(prod).ConfigItem.ConfigItem
    assert it == parent[0]

    assert it.X.aa == 1
    assert it.Y.aa == 37
    assert it.Y.bb == it.X
    assert it.Y.cc is None
