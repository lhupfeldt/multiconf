# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem
from multiconf.envs import EnvFactory
from multiconf.decorators import named_as


def test():
    @named_as('x')
    class X(ConfigItem):
        def __init__(self):
            super().__init__()
            self.aa = 0
            self.bb = 0
            self.ttt = 1

        @property
        def paa(self):
            # print("In 'paa'")
            return 1

        @property
        def pbb(self):
            # print("In 'pbb'")
            return 2

    ef = EnvFactory()
    pp = ef.Env('pp')
    prod = ef.Env('prod')

    @mc_config(ef, load_now=True)
    def config(root):
        with ConfigItem() as cr:
            with X() as x:
                # x.setattr('ttt', prod=17)
                x.setattr('aa', pp=11, prod=22)
                x.setattr('paa', mc_overwrite_property=True, pp=33)
                x.bb = 17

                with X() as y:
                    y.setattr('aa', pp=12, prod=23)
                    y.setattr('paa', mc_overwrite_property=True, pp=34)
                    y.bb = 18


    def dump(cfg, other_env):
        print()
        cfg = cfg.ConfigItem

        aa = cfg.x.aa
        bb = cfg.x.bb
        paa = cfg.x.paa
        pbb = cfg.x.pbb
        print("get current: {cfg}, aa: {aa}, bb: {bb}, paa: {paa}, pbb: {pbb}".format(cfg=cfg, aa=aa, bb=bb, paa=paa, pbb=pbb))

        yaa = cfg.x.x.aa
        ybb = cfg.x.x.bb
        ypaa = cfg.x.x.paa
        ypbb = cfg.x.x.pbb
        print("get current: {cfg}, yaa: {yaa}, ybb: {ybb}, ypaa: {ypaa}, ypbb: {ypbb}".format(cfg=cfg, yaa=yaa, ybb=ybb, ypaa=ypaa, ypbb=ypbb))

        oaa = cfg.x.getattr('aa', other_env)
        obb = cfg.x.getattr('bb', other_env)
        print("get {cfg} other({other}) attr: aa: {aa}, bb: {bb}".format(cfg=cfg, other=other_env, aa=oaa, bb=obb))

        opaa = cfg.x.getattr('paa', other_env)
        opbb = cfg.x.getattr('pbb', other_env)
        print("get {cfg} other({other}) @property: paa: {paa}, pbb: {pbb}".format(cfg=cfg, other=other_env, paa=opaa, pbb=opbb))

        return aa, bb, paa, pbb, oaa, obb, opaa, opbb, yaa, ybb, ypaa, ypbb

    prod_cfg = config(prod)
    pp_cfg = config(pp)

    res = dump(prod_cfg, pp)
    assert res == (22, 17, 1, 2, 11, 17, 33, 2, 23, 18, 1, 2)

    del prod_cfg

    res = dump(pp_cfg, prod)
    assert res == (11, 17, 33, 2, 22, 17, 1, 2, 12, 18, 34, 2)


    print()
    try:
        pp_cfg.x.q
    except Exception as ex:
        print(ex)

    try:
        pp_cfg.x.getattr('z', prod)
    except Exception as ex:
        print(ex)

    try:
        @mc_config(ef, ConfigItem, load_now=True)
        def config(root):
            with root as cr:
                print("in config method - loading:", cr)
                with X() as x:
                    x.setattr('aa', mc_overwrite_property=True, pp=11, prod=22)
                    x.bb = 17

    except Exception as ex:
        print(ex)
