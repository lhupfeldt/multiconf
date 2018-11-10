# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA


ef = EnvFactory()

envs = []
num_envs_per_group = 128

groups = []
num_groups = 16

for ii in range(0, num_groups):
    local_envs = []
    for jj in range(0, num_envs_per_group):
        local_envs.append(ef.Env('e' + str(ii) + '_' + str(jj)))
    groups.append(ef.EnvGroup('g' + str(ii), *local_envs))
    envs.extend(local_envs)


class ItemWithManyAttributes(ItemWithAA):
    def __init__(self, aa=MC_REQUIRED):
        super().__init__(aa=aa)
        self.b = MC_REQUIRED
        self.c = None
        self.d = None
        self.e = None
        self.f = None
        self.g = None
        self.h = None
        self.i = MC_REQUIRED


def test_many_envs():
    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithManyAttributes() as conf:
            conf.setattr('aa', default=None, e0_0=0)
            conf.setattr('b', default=None, e1_7=1)
            conf.setattr('c', default=None, e2_15=2)
            conf.setattr('d', default=None, e3_23=3)
            conf.setattr('e', default=None, e4_31=4)
            conf.setattr('f', default=None, e5_39=5)
            conf.setattr('g', default=None, e6_47=6)
            conf.setattr('h', default=None, e7_55=7)
            conf.setattr('i', default=None, e0_0=10, e15_127=8)

    conf = config(envs[0]).ItemWithManyAttributes
    assert conf.aa == 0
    assert conf.b is None
    assert conf.i == 10


def test_many_groups():
    # This is slow!
    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithManyAttributes() as conf:
            conf.setattr('aa', default=None, g0=0)
            conf.setattr('b', default=None, g1=1)
            conf.setattr('i', default=None, e0_0=10, g15=8)

    conf = config(envs[0]).ItemWithManyAttributes
    assert conf.aa == 0
    assert conf.b is None
    assert conf.i == 10
