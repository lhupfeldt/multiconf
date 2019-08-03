# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.envs import EnvFactory
from multiconf import mc_config, ConfigItem, MC_REQUIRED


efac = EnvFactory()
pp = efac.Env('pp')
prod = efac.Env('prod')


def test_mc_init_inherited():
    class XBase(ConfigItem):
        def __init__(self):
            super().__init__()
            self.version = MC_REQUIRED

        def mc_init(self):
            super().mc_init()
            self.version = 1

    class X1(XBase):
        def mc_init(self):
            super().mc_init()
            self.version = 2

    class X2(XBase):
        def mc_init(self):
            super().mc_init()
            self.setattr('version', prod=3)

    @mc_config(efac, load_now=True)
    def config(_):
        with ConfigItem():
            X1()
            X2()

    project = config(prod).ConfigItem
    print("project.X1.version:", project.X1.version)
    assert project.X1.version == 2
    assert project.X2.version == 3

    @mc_config(efac, load_now=True)
    def config(_):
        with ConfigItem():
            X1()
            X2()

    project = config(pp).ConfigItem
    assert project.X1.version == 2
    assert project.X2.version == 1
