# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, MC_REQUIRED
from ..envs import EnvFactory

from .utils.tstclasses import RootWithAA

ef = EnvFactory()

envs = []
groups = []
for ii in range(0, 16):
    local_envs = []
    for jj in range(0, 128):
        local_envs.append(ef.Env('e' + str(ii) + '_' + str(jj)))
    groups.append(ef.EnvGroup('g' + str(ii), *local_envs))
    envs.extend(local_envs)


class RootWithManyAttributes(RootWithAA):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                 mc_allow_todo=False, mc_allow_current_env_todo=False,
                 aa=MC_REQUIRED):
        super(RootWithManyAttributes, self).__init__(
            selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
            mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo,
            aa=aa)
        self.b = MC_REQUIRED
        self.c = None
        self.d = None
        self.e = None
        self.f = None
        self.g = None
        self.h = None
        self.i = MC_REQUIRED


def test_many_envs():
    with RootWithManyAttributes(envs[0], ef) as conf:
        conf.setattr('aa', default=None, e0_0=0)
        conf.setattr('b', default=None, e1_7=1)
        conf.setattr('c', default=None, e2_15=2)
        conf.setattr('d', default=None, e3_23=3)
        conf.setattr('e', default=None, e4_31=4)
        conf.setattr('f', default=None, e5_39=5)
        conf.setattr('g', default=None, e6_47=6)
        conf.setattr('h', default=None, e7_55=7)
        conf.setattr('i', default=None, e0_0=10, e15_127=8)

    assert conf.aa == 0
    assert conf.b is None
    assert conf.i == 10


def test_many_groups():
    # This is slow!
    with RootWithManyAttributes(envs[0], ef) as conf:
        conf.setattr('aa', default=None, g0=0)
        conf.setattr('b', default=None, g1=1)
        conf.setattr('i', default=None, e0_0=10, g15=8)

    assert conf.aa == 0
    assert conf.b is None
    assert conf.i == 10
