# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf.envs import EnvFactory, AmbiguousEnvException


ef = EnvFactory()
dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
dev3 = ef.Env('dev3')
g_dev12 = ef.EnvGroup('g_dev12', dev1, dev2)
g_dev23 = ef.EnvGroup('g_dev23', dev2, dev3)
g_dev13 = ef.EnvGroup('g_dev13', dev1, dev3)
g_dev12_3 = ef.EnvGroup('g_dev12_3', g_dev12, dev3)

ef._mc_calc_env_group_order()


def test_env_directly_in_list(capsys):
    assert ef._mc_select_env_list(dev1, [g_dev12_3, dev1, g_dev12], [g_dev12, dev2, dev3]) == 1
    assert ef._mc_select_env_list(dev1, [g_dev12_3, dev3, dev2], [dev1, g_dev12_3]) == 2
    assert ef._mc_select_env_list(dev1, [g_dev12_3, dev1, g_dev12], []) == 1
    assert ef._mc_select_env_list(dev1, [], [dev1, g_dev12_3]) == 2

    sout, serr = capsys.readouterr()
    assert sout == ""
    assert serr == ""


def test_env_not_in_list(capsys):
    assert ef._mc_select_env_list(dev3, [dev1, g_dev12], [g_dev12, dev2]) is None
    assert ef._mc_select_env_list(dev3, [dev1, g_dev12], []) is None
    assert ef._mc_select_env_list(dev3, [], [g_dev12, dev2]) is None
    assert ef._mc_select_env_list(dev3, [], []) is None

    sout, serr = capsys.readouterr()
    assert sout == ""
    assert serr == ""


def test_env_in_list_through_group(capsys):
    assert ef._mc_select_env_list(dev1, [g_dev12_3, g_dev12], [g_dev23, dev2, dev3]) == 1
    assert ef._mc_select_env_list(dev1, [g_dev23, dev2, dev3], [g_dev12_3]) == 2
    assert ef._mc_select_env_list(dev1, [g_dev12_3], [g_dev12, dev2, dev3]) == 2

    sout, serr = capsys.readouterr()
    assert sout == ""
    assert serr == ""


def test_env_directly_in_list_ambiguous():
    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_select_env_list(dev1, [dev1], [dev1])

    assert "Ambiguous env select for 'Env('dev1')'." in str(exinfo.value)
    assert exinfo.value.ambiguous == [dev1, dev1]

    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_select_env_list(dev1, [g_dev12_3, dev1, g_dev12], [g_dev12, dev2, dev3, dev1])

    assert "Ambiguous env select for 'Env('dev1')'." in str(exinfo.value)
    assert exinfo.value.ambiguous == [dev1, dev1]

    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_select_env_list(dev3, [g_dev12_3, dev3, dev2], [dev1, g_dev12_3, dev3])

    assert "Ambiguous env select for 'Env('dev3')'." in str(exinfo.value)
    assert exinfo.value.ambiguous == [dev3, dev3]


def test_env_in_list_through_same_group_ambiguous():
    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_select_env_list(dev1, [g_dev12_3, g_dev12], [g_dev12, dev2, dev3])

    assert "Ambiguous env select for 'Env('dev1')'." in str(exinfo.value)
    assert exinfo.value.ambiguous == [g_dev12, g_dev12]

    with raises(AmbiguousEnvException) as exinfo:
        ef._mc_select_env_list(dev1, [g_dev12_3], [dev2, dev3, g_dev12_3])

    assert "Ambiguous env select for 'Env('dev1')'." in str(exinfo.value)
    assert exinfo.value.ambiguous == [g_dev12_3, g_dev12_3]


def test_env_in_list_through_different_groups_ambiguousxo():
    with raises(AmbiguousEnvException) as exinfo:
        res = ef._mc_select_env_list(dev1, [g_dev12_3, g_dev13], [g_dev12, dev2, dev3])
        print("dev1.lookup_order", dev1.lookup_order)
        print(res)

    with raises(AmbiguousEnvException) as exinfo:
        res = ef._mc_select_env_list(dev1, [g_dev12_3, g_dev12], [g_dev13, dev2, dev3])
        print(dev1.lookup_order)
        print(res)

    assert "Ambiguous env select for 'Env('dev1')'." in str(exinfo.value)
    assert exinfo.value.ambiguous == [g_dev12, g_dev13]
