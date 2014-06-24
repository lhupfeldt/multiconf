# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot
from ..envs import EnvFactory

ef = EnvFactory()

envs = []
groups = []
for ii in range(0, 16):
    local_envs = []
    for jj in range(0, 128):
        local_envs.append(ef.Env('e' + str(ii) + '_' + str(jj)))
    groups.append(ef.EnvGroup('g' + str(ii), *local_envs))
    envs.extend(local_envs)


def test_many_envs():
    with ConfigRoot(envs[0], envs) as conf:
        conf.setattr('a', default=None, e0_0=0)
        conf.setattr('b', default=None, e1_7=1)
        conf.setattr('c', default=None, e2_15=2)
        conf.setattr('d', default=None, e3_23=3)
        conf.setattr('e', default=None, e4_31=4)
        conf.setattr('f', default=None, e5_39=5)
        conf.setattr('g', default=None, e6_47=6)
        conf.setattr('h', default=None, e7_55=7)
        conf.setattr('i', default=None, e0_0=10, e15_127=8)

    assert conf.a == 0
    assert conf.b == None
    assert conf.i == 10


def test_many_groups():
    # This is slow!
    with ConfigRoot(envs[0], envs) as conf:
        conf.setattr('a', default=None, g0=0)
        conf.setattr('b', default=None, g1=1)
        conf.setattr('i', default=None, e0_0=10, g15=8)

    assert conf.a == 0
    assert conf.b == None
    assert conf.i == 10
