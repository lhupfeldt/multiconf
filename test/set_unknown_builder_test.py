# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, ConfigBuilder, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.utils import config_error


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_pp = EnvFactory()
pp2 = ef2_prod_pp.Env('pp')
prod2 = ef2_prod_pp.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


class strict_project(ConfigItem):
    def __init__(self):
        super().__init__()
        self.a = None
        self.b = MC_REQUIRED


class StrictItem(ConfigItem):
    def __init__(self):
        super().__init__()
        self.x = MC_REQUIRED
        self.y = None


class BuilderStrictItem(ConfigBuilder):
    def __init__(self):
        super().__init__()
        self.x = MC_REQUIRED
        self.y = None

    def mc_build(self):
        super().mc_build()
        with StrictItem() as si:
            si.x = self.x


def test_setattr_strict_builder_ok():
    bsi = [None]

    @mc_config(ef2_prod_pp, load_now=True)
    def config(_):
        with strict_project() as sp:
            sp.a = 1
            sp.setattr('b', default=2)

            with BuilderStrictItem() as bb:
                bb.x = 1
                bb.setattr('y', default='yes')
            bsi[0] = bb

    sp = config(prod2).strict_project
    assert bsi[0].x == 1
    assert bsi[0].y == 'yes'
    assert sp.StrictItem.x == 1


def test_setunknown_strict_builder_ok():
    bsi = [None]

    @mc_config(ef2_prod_pp, load_now=True)
    def config(_):
        with strict_project() as sp:
            sp.b = 1
            sp.setattr('c', default=2, mc_set_unknown=True)

            with BuilderStrictItem() as bb:
                bb.x = 1
                bb.setattr('z', default='yes', mc_set_unknown=True)
            bsi[0] = bb

    sp = config(prod2).strict_project
    assert bsi[0].x == 1
    assert bsi[0].z == 'yes'
    assert sp.StrictItem.x == 1
