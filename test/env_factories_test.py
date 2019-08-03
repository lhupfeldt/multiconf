# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


# pylint: disable=E0611
from pytest import raises

from multiconf.envs import EnvFactory, AmbiguousEnvException


def _names(groups):
    return [gg.name for gg in groups]


def _lookup_order(env):
    act = []
    for gg in env.lookup_order:
        act.append((gg.name, _names(gg.ambiguous[env.name])))
    return act


def test_mc_calc_env_group_order():
    ef = EnvFactory()

    d0 = ef.Env('d0')

    d1a = ef.Env('d1a')
    d1b = ef.Env('d1b')
    d1c = ef.Env('d1c')

    d2a = ef.Env('d2a')
    d2b = ef.Env('d2b')
    d2c = ef.Env('d2c')

    g_d1ab_d2a = ef.EnvGroup('g_d1ab_d2a', d1a, d1b, d2a)  # No d2b
    g_d1b_d2ab = ef.EnvGroup('g_d1b_d2ab', d1b, d2a, d2b)  # No d1a
    g_d1ab_d2a_d1cd2c = ef.EnvGroup('g_d1ab_d2a_d1cd2c', g_d1ab_d2a, d1c, d2c)

    d3a = ef.Env('d3a')
    d3b = ef.Env('d3b')
    d3c = ef.Env('d3c')

    g_d3ab = ef.EnvGroup('g_d3ab', d3a, d3b)
    g_d3ab_d3c = ef.EnvGroup('g_d3', g_d3ab, d3c)

    g_d1_overlap1 = ef.EnvGroup('g_d1_overlap1', d1a)
    g_d1_overlap2 = ef.EnvGroup('g_d1_overlap2', d1a)

    g_d13_overlap1 = ef.EnvGroup('g_d13_overlap1', d1a, d3a)
    g_d13_overlap2 = ef.EnvGroup('g_d13_overlap2', d1b, d3b)
    g_d13_overlap3 = ef.EnvGroup('g_d13_overlap3', d1a, d3b)

    pp = ef.Env('pp')
    prod = ef.Env('prod')
    g_prod = ef.EnvGroup('g_prod', pp, prod)

    ef._mc_calc_env_group_order()

    for env_name, env in ef.envs.items():
        print()
        print(env_name + ':', env.lookup_order)

    # Test d0 lookup order (env in no groups)
    assert _lookup_order(d0) == [('default', [])]

    # Test d1a
    assert _lookup_order(d1a) == [
        (g_d1ab_d2a.name, _names([g_d1_overlap1, g_d1_overlap2, g_d13_overlap1, g_d13_overlap3])),
        (g_d1ab_d2a_d1cd2c.name, _names([g_d1_overlap1, g_d1_overlap2, g_d13_overlap1, g_d13_overlap3])),
        (g_d1_overlap1.name, _names([g_d1_overlap2, g_d13_overlap1, g_d13_overlap3])),
        (g_d1_overlap2.name, _names([g_d13_overlap1, g_d13_overlap3])),
        (g_d13_overlap1.name, _names([g_d13_overlap3])),
        (g_d13_overlap3.name, []),
        ('default', []),
        ]

    # Test d1b
    assert _lookup_order(d1b) == [
        (g_d1ab_d2a.name, _names([g_d1b_d2ab, g_d13_overlap2])),
        (g_d1b_d2ab.name, _names([g_d1ab_d2a_d1cd2c, g_d13_overlap2])),
        (g_d1ab_d2a_d1cd2c.name, _names([g_d13_overlap2])),
        (g_d13_overlap2.name, []),
        ('default', []),
    ]

    # Test d1c
    assert _lookup_order(d1c) == [
        (g_d1ab_d2a_d1cd2c.name, []),
        ('default', []),
    ]

    # Test d2a
    assert _lookup_order(d2a) == [
        (g_d1ab_d2a.name, _names([g_d1b_d2ab])),
        (g_d1b_d2ab.name, _names([g_d1ab_d2a_d1cd2c])),
        (g_d1ab_d2a_d1cd2c.name, []),
        ('default', []),
    ]

    # Test d2b
    assert _lookup_order(d2b) == [
        (g_d1b_d2ab.name, []),
        ('default', []),
    ]

    # Test d2c
    assert _lookup_order(d2c) == [
        (g_d1ab_d2a_d1cd2c.name, []),
        ('default', []),
    ]

    # Test d3a
    assert _lookup_order(d3a) == [
        (g_d3ab.name, _names([g_d13_overlap1])),
        (g_d3ab_d3c.name, _names([g_d13_overlap1])),
        (g_d13_overlap1.name, []),
        ('default', []),
    ]

    # Test d3b
    assert _lookup_order(d3b) == [
        (g_d3ab.name, _names([g_d13_overlap2, g_d13_overlap3])),
        (g_d3ab_d3c.name, _names([g_d13_overlap2, g_d13_overlap3])),
        (g_d13_overlap2.name, _names([g_d13_overlap3])),
        (g_d13_overlap3.name, []),
        ('default', []),
    ]

    # Some skipped ...

    # Test pp
    assert _lookup_order(pp) == [
        (g_prod.name, []),
        ('default', []),
    ]

    # Test prod
    assert _lookup_order(prod) == [
        (g_prod.name, []),
        ('default', []),
    ]


def test_mc_resolve_env_group_value():
    ef = EnvFactory()

    d0 = ef.Env('d0')

    d1a = ef.Env('d1a')
    d1b = ef.Env('d1b')
    d1c = ef.Env('d1c')

    d2a = ef.Env('d2a')
    d2b = ef.Env('d2b')
    d2c = ef.Env('d2c')

    g_d1ab_d2a = ef.EnvGroup('g_d1ab_d2a', d1a, d1b, d2a)  # No d2b
    g_d1b_d2ab = ef.EnvGroup('g_d1b_d2ab', d1b, d2a, d2b)  # No d1a
    g_d1ab_d2a_d1cd2c = ef.EnvGroup('g_d1ab_d2a_d1cd2c', g_d1ab_d2a, d1c, d2c)

    d3a = ef.Env('d3a')
    d3b = ef.Env('d3b')
    d3c = ef.Env('d3c')

    g_d3ab = ef.EnvGroup('g_d3ab', d3a, d3b)
    g_d3ab_d3c = ef.EnvGroup('g_d3', g_d3ab, d3c)

    g_d1_overlap1 = ef.EnvGroup('g_d1_overlap1', d1a)
    g_d1_overlap2 = ef.EnvGroup('g_d1_overlap2', d1a)

    g_d13_overlap1 = ef.EnvGroup('g_d13_overlap1', d1a, d3a)
    g_d13_overlap2 = ef.EnvGroup('g_d13_overlap2', d1b, d3b)
    g_d13_overlap3 = ef.EnvGroup('g_d13_overlap3', d1a, d3b)

    pp = ef.Env('pp')
    prod = ef.Env('prod')
    g_prod = ef.EnvGroup('g_prod', pp, prod)

    ef._mc_calc_env_group_order()

    assert ef._mc_resolve_env_group_value(d0, dict(d0=1)) == (1, d0)
    assert ef._mc_resolve_env_group_value(d0, dict(d0=1, d1a=17)) == (1, d0)

    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, d1a=17)) == (17, d1a)
    # TODO: check from_eg
    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, d1a=17, g_d1ab_d2a=3))[0] == 17
    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, g_d1ab_d2a=17))[0] == 17
    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, g_d1ab_d2a=17, g_d1ab_d2a_d1cd2c=3))[0] == 17
    assert ef._mc_resolve_env_group_value(d1a, dict(g_d1ab_d2a_d1cd2c=3, d0=1, g_d1ab_d2a=17))[0] == 17
    assert ef._mc_resolve_env_group_value(d1a, dict(g_d1ab_d2a_d1cd2c=3))[0] == 3
    assert ef._mc_resolve_env_group_value(d1a, dict(g_d1ab_d2a_d1cd2c=3))[0] == 3
    assert ef._mc_resolve_env_group_value(d1a, dict(g_d1ab_d2a_d1cd2c=3, default=7))[0] == 3
    assert ef._mc_resolve_env_group_value(d1a, dict(default=7))[0] == 7

    assert ef._mc_resolve_env_group_value(prod, dict(d0=1, prod=18))[0] == 18
    assert ef._mc_resolve_env_group_value(prod, dict(d0=1, d1a=17, prod=18))[0] == 18
    assert ef._mc_resolve_env_group_value(prod, dict(d0=1, d1a=17, g_prod=19, prod=18))[0] == 18
    assert ef._mc_resolve_env_group_value(prod, dict(d0=1, d1a=17, g_d1ab_d2a=3, g_prod=19, prod=18))[0] == 18
    assert ef._mc_resolve_env_group_value(prod, dict(g_prod=19, prod=18, d0=1, g_d1ab_d2a=17))[0] == 18
    assert ef._mc_resolve_env_group_value(prod, dict(d0=1, g_d1ab_d2a=17, g_d1ab_d2a_d1cd2c=3, g_prod=19, prod=18))[0] == 18
    assert ef._mc_resolve_env_group_value(prod, dict(d0=1, g_d1ab_d2a=17, g_d1ab_d2a_d1cd2c=3, g_prod=19))[0] == 19
    assert ef._mc_resolve_env_group_value(prod, dict(g_d1ab_d2a_d1cd2c=3, d0=1, g_d1ab_d2a=17, default=18))[0] == 18

    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, prod=18, g_d13_overlap1=20))[0] == 20
    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, d1a=17, prod=18, g_d13_overlap1=20))[0] == 17
    assert ef._mc_resolve_env_group_value(d1a, dict(g_d13_overlap1=20, d0=1, g_prod=19, prod=18))[0] == 20
    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, g_d13_overlap1=20, g_prod=19, prod=18))[0] == 20
    assert ef._mc_resolve_env_group_value(d1a, dict(g_prod=19, prod=18, d0=1, g_d13_overlap1=20))[0] == 20
    assert ef._mc_resolve_env_group_value(d1a, dict(d0=1, g_prod=19, prod=18, g_d13_overlap1=20))[0] == 20

    assert ef._mc_resolve_env_group_value(d3b, dict(d0=1, prod=18, g_d13_overlap1=20, g_d13_overlap2=21))[0] == 21
    assert ef._mc_resolve_env_group_value(d3b, dict(d0=1, d1a=17, prod=18, g_d13_overlap1=20, g_d13_overlap2=21))[0] == 21
    assert ef._mc_resolve_env_group_value(d3b, dict(g_d13_overlap2=21, g_d13_overlap1=20, d0=1, d1a=17, g_prod=19, prod=18))[0] == 21
    assert ef._mc_resolve_env_group_value(d3b, dict(d0=1, g_d13_overlap2=21, g_d13_overlap1=20, d1a=17, g_d1ab_d2a=3, g_prod=19, prod=18))[0] == 21
    assert ef._mc_resolve_env_group_value(d3b, dict(g_prod=19, prod=18, d0=1, g_d13_overlap2=21, g_d1ab_d2a=17, g_d13_overlap1=20))[0] == 21
    assert ef._mc_resolve_env_group_value(d3b, dict(d0=1, g_d1ab_d2a=17, g_d1ab_d2a_d1cd2c=3, g_prod=19, prod=18, g_d13_overlap1=20, g_d13_overlap2=21))[0] == 21
    assert ef._mc_resolve_env_group_value(d3b, dict(d0=1, g_d1ab_d2a=17, g_d13_overlap1=20, g_d1ab_d2a_d1cd2c=3, g_prod=19, g_d13_overlap2=21))[0] == 21
    assert ef._mc_resolve_env_group_value(d3b, dict(g_d1ab_d2a_d1cd2c=3, d0=1, g_d1ab_d2a=17, g_d13_overlap1=20, default=18, g_d13_overlap2=21))[0] == 21


def test_mc_resolve_env_group_value_missing():
    ef = EnvFactory()

    d0 = ef.Env('d0')

    d1a = ef.Env('d1a')
    d1b = ef.Env('d1b')
    d1c = ef.Env('d1c')

    d2a = ef.Env('d2a')
    d2b = ef.Env('d2b')
    d2c = ef.Env('d2c')

    g_d1ab_d2a = ef.EnvGroup('g_d1ab_d2a', d1a, d1b, d2a)  # No d2b
    g_d1b_d2ab = ef.EnvGroup('g_d1b_d2ab', d1b, d2a, d2b)  # No d1a
    g_d1ab_d2a_d1cd2c = ef.EnvGroup('g_d1ab_d2a_d1cd2c', g_d1ab_d2a, d1c, d2c)

    d3a = ef.Env('d3a')
    d3b = ef.Env('d3b')
    d3c = ef.Env('d3c')

    g_d3ab = ef.EnvGroup('g_d3ab', d3a, d3b)
    g_d3ab_d3c = ef.EnvGroup('g_d3', g_d3ab, d3c)

    g_d1_overlap1 = ef.EnvGroup('g_d1_overlap1', d1a)
    g_d1_overlap2 = ef.EnvGroup('g_d1_overlap2', d1a)

    g_d13_overlap1 = ef.EnvGroup('g_d13_overlap1', d1a, d3a)
    g_d13_overlap2 = ef.EnvGroup('g_d13_overlap2', d1b, d3b)
    g_d13_overlap3 = ef.EnvGroup('g_d13_overlap3', d1a, d3b)

    pp = ef.Env('pp')
    prod = ef.Env('prod')
    g_prod = ef.EnvGroup('g_prod', pp, prod)

    ef._mc_calc_env_group_order()

    val, gg = ef._mc_resolve_env_group_value(prod, dict(d0=1, g_d1ab_d2a=3, g_d13_overlap1=7))
    assert gg is None

    val, gg = ef._mc_resolve_env_group_value(pp, dict(d0=1, g_d1ab_d2a=17, g_d1ab_d2a_d1cd2c=3, g_d1b_d2ab=9))
    assert gg is None

    val, gg = ef._mc_resolve_env_group_value(
        prod, dict(g_d1ab_d2a_d1cd2c=3, d0=1, g_d1ab_d2a=1, g_d1_overlap1=1, g_d1_overlap2=1, g_d13_overlap1=1, g_d13_overlap3=1, pp=9))
    assert gg is None


def test_mc_resolve_env_group_value_ambiguous():
    ef = EnvFactory()

    d0 = ef.Env('d0')

    d1a = ef.Env('d1a')
    d1b = ef.Env('d1b')
    d1c = ef.Env('d1c')

    d2a = ef.Env('d2a')
    d2b = ef.Env('d2b')
    d2c = ef.Env('d2c')

    g_d1ab_d2a = ef.EnvGroup('g_d1ab_d2a', d1a, d1b, d2a)  # No d2b
    g_d1b_d2ab = ef.EnvGroup('g_d1b_d2ab', d1b, d2a, d2b)  # No d1a
    g_d1ab_d2a_d1cd2c = ef.EnvGroup('g_d1ab_d2a_d1cd2c', g_d1ab_d2a, d1c, d2c)

    d3a = ef.Env('d3a')
    d3b = ef.Env('d3b')
    d3c = ef.Env('d3c')

    g_d3ab = ef.EnvGroup('g_d3ab', d3a, d3b)
    g_d3ab_d3c = ef.EnvGroup('g_d3', g_d3ab, d3c)

    g_d1_overlap1 = ef.EnvGroup('g_d1_overlap1', d1a)
    g_d1_overlap2 = ef.EnvGroup('g_d1_overlap2', d1a)

    g_d13_overlap1 = ef.EnvGroup('g_d13_overlap1', d1a, d3a)
    g_d13_overlap2 = ef.EnvGroup('g_d13_overlap2', d1b, d3b)
    g_d13_overlap3 = ef.EnvGroup('g_d13_overlap3', d1a, d3b)

    pp = ef.Env('pp')
    prod = ef.Env('prod')
    g_prod = ef.EnvGroup('g_prod', pp, prod)

    ef._mc_calc_env_group_order()

    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_resolve_env_group_value(d1a, dict(d0=1, g_d1ab_d2a=3, g_d13_overlap1=7))
    assert str(exinfo.value) == "Ambiguous values for: Env('d1a')"
    assert exinfo.value.ambiguous == [g_d1ab_d2a, g_d13_overlap1]

    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_resolve_env_group_value(d2a, dict(d0=1, g_d1ab_d2a=17, g_d1ab_d2a_d1cd2c=3, g_d1b_d2ab=9))
    assert exinfo.value.ambiguous == [g_d1ab_d2a, g_d1b_d2ab]

    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_resolve_env_group_value(d1a, dict(g_d1ab_d2a_d1cd2c=3, d0=1, g_d1ab_d2a=1, g_d1_overlap1=1, g_d1_overlap2=1, g_d13_overlap1=1, g_d13_overlap3=1, pp=9))
    assert exinfo.value.ambiguous == [g_d1ab_d2a, g_d1_overlap1, g_d1_overlap2, g_d13_overlap1, g_d13_overlap3]
