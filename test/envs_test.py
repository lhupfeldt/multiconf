# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from ..envs import EnvFactory

ef = EnvFactory()

envs_only = []

dev2ct = ef.Env('dev2CT')
dev2st = ef.Env('dev2ST')
envs_only.extend((dev2ct, dev2st))
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3CT')
dev3st = ef.Env('dev3ST')
envs_only.extend((dev3ct, dev3st))
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
envs_only.extend((pp, prod))
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)

groups_only = [valid_envs, g_dev, g_dev2, g_dev3, g_prod]
all_envs = groups_only + envs_only

valid_envs_repr = """
EnvGroup('g_all') {
     EnvGroup('g_dev') {
       EnvGroup('g_dev2') {
         Env('dev2CT'),
         Env('dev2ST')
    },
       EnvGroup('g_dev3') {
         Env('dev3CT'),
         Env('dev3ST')
    }
  },
     EnvGroup('g_prod') {
       Env('pp'),
       Env('prod')
  }
}
"""


def test_repr_of_valid_envs():
    assert repr(valid_envs) == valid_envs_repr.strip()


def test_membership():
    # Env is in itself
    assert prod in prod
    # Group is in itself
    assert g_dev in g_dev

    assert prod in valid_envs
    assert prod not in g_dev
    assert g_dev not in g_prod
    assert dev2ct in g_dev2
    assert dev2ct in g_dev
    assert dev2ct not in g_dev3
    assert g_dev2 in g_dev
    assert g_dev not in g_dev2


def test_iterating_envs_only():
    envs = []
    for env in valid_envs.envs():
        envs.append(env)
    assert envs == envs_only


def test_iterating_groups_only():
    groups = []
    for group in valid_envs.groups():
        groups.append(group)
    assert groups == groups_only


def test_iterating_groups_and_envs():
    envs = []
    for env in valid_envs.all():
        envs.append(env)
    assert envs == all_envs


def test_as_key():
    envs = {}
    for env in valid_envs.all():
        envs[env] = True
    for env in valid_envs.all():
        assert envs[env] == True


def test_env_from_string():
    assert ef.env("dev2CT").name == "dev2CT"


def test_group_from_string():
    assert ef.group("g_dev2").name == "g_dev2"


def test_env_or_group_from_string():
    assert ef.env_or_group("dev2CT").name == "dev2CT"
    assert ef.env_or_group("g_dev2").name == "g_dev2"
