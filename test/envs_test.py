# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf.envs import EnvFactory, EnvException


ef = EnvFactory()

envs_only = []

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
envs_only.extend((dev1, dev2))
g_dev12 = ef.EnvGroup('g_dev12', dev1, dev2)

tst1 = ef.Env('tst1')
tst2 = ef.Env('tst2')
envs_only.extend((tst1, tst2))
g_tst = ef.EnvGroup('g_tst', tst1, tst2)

g_dev_tst = ef.EnvGroup('g_dev_tst', g_dev12, g_tst)

pp = ef.Env('pp')
prod = ef.Env('prod')
envs_only.extend((pp, prod))
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev_tst, g_prod)

groups_only = [valid_envs, g_dev_tst, g_dev12, g_tst, g_prod]

valid_envs_repr = """
EnvGroup('g_all') {
   EnvGroup('g_dev_tst') {
      EnvGroup('g_dev12') {
         Env('dev1'),
         Env('dev2')
      },
      EnvGroup('g_tst') {
         Env('tst1'),
         Env('tst2')
      }
   },
   EnvGroup('g_prod') {
      Env('pp'),
      Env('prod')
   }
}
"""


def test_repr_of_valid_envs():
    print(repr(valid_envs))
    assert repr(valid_envs) == valid_envs_repr.strip()


def test_eq():
    # Compare Envs
    assert prod == prod
    assert dev1 == dev1
    assert prod != dev1
    assert dev1 != prod

    # Compare Groups
    assert g_dev_tst == g_dev_tst
    assert g_prod == g_prod
    assert g_dev_tst != g_prod
    assert g_prod != g_dev_tst

    # Compare Groups to Envs
    assert g_dev_tst != dev1
    assert g_prod != prod
    assert dev1 != g_dev_tst
    assert prod != g_prod

    # Compare to other types
    assert g_dev_tst is not None
    assert g_prod != 1
    assert dev1 is not None
    assert prod != "Hello"
    assert not prod == "Hello"

    # Compare other types to self
    assert g_dev_tst is not None
    assert 1 != g_prod
    assert dev1 is not None
    assert "Hello" != prod


def test_membership():
    # Env is not in itself
    assert prod not in prod
    # Group is not in itself
    assert g_dev_tst not in g_dev_tst

    assert prod in valid_envs
    assert prod not in g_dev_tst
    assert g_dev_tst not in g_prod
    assert dev1 in g_dev12
    assert dev1 in g_dev_tst
    assert dev1 not in g_tst
    assert g_dev12 in g_dev_tst
    assert g_dev_tst not in g_dev12


def test_iterating_envs_only():
    envs = []
    for env in valid_envs.envs:
        envs.append(env)
    assert envs == envs_only


def test_iterating_groups_only():
    groups = []
    for group in valid_envs.groups:
        groups.append(group)
    assert groups == groups_only


def test_as_key():
    envs = {}
    for env in valid_envs.envs + valid_envs.groups:
        envs[env] = True
    for env in valid_envs.envs + valid_envs.groups:
        assert envs[env]


def test_env_from_name():
    assert ef.env("dev1").name == "dev1"

    with raises(EnvException) as exinfo:
        ef.env("g_dev_tst")
    assert str(exinfo.value) == "No such Env: 'g_dev_tst'"

    with raises(EnvException) as exinfo:
        ef.env("no-way")
    assert str(exinfo.value) == "No such Env: 'no-way'"


def test_env_or_group_from_name():
    assert ef.env_or_group_from_name("dev1").name == "dev1"
    assert ef.env_or_group_from_name("g_dev_tst").name == "g_dev_tst"

    with raises(EnvException) as exinfo:
        ef.env_or_group_from_name("no-way")
    assert str(exinfo.value) == "No such Env or EnvGroup: 'no-way'"


def test_repeated_nested_env_member():
    efl = EnvFactory()
    hh1 = efl.Env('hh1')
    hh2 = efl.EnvGroup('hh2', hh1)
    hh3 = efl.EnvGroup('hh3', hh1, hh2)

    assert hh3.envs == [hh1]


def test_env_factory_in_use(capsys):
    with raises(EnvException) as exinfo:
        myef = EnvFactory()
        mydev1 = myef.Env('dev1')
        myef._mc_calc_env_group_order()
        myef.EnvGroup('g_dev12', mydev1)

    sout, serr = capsys.readouterr()
    assert sout == ''
    assert str(exinfo.value) == "EnvFactory is already in use. No more groups may be added."
    assert serr == ''  # TODO empty error message

    with raises(EnvException) as exinfo:
        myef = EnvFactory()
        mydev1 = myef.Env('dev1')
        myef._mc_calc_env_group_order()
        myef.Env('dev2')

    _sout, serr = capsys.readouterr()
    assert str(exinfo.value) == "EnvFactory is already in use. No more envs may be added."
    assert serr == ''  # TODO empty error message


def test_group_members_not_same_factory(capsys):
    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        mydev1 = myef1.Env('dev1')
        myef2 = EnvFactory()
        mydev2 = myef1.Env('dev2')
        myef2.EnvGroup('g_dev12', mydev1, mydev2)

    _sout, serr = capsys.readouterr()
    assert str(exinfo.value) == "EnvGroup: The group members must be from the same 'env_factory' as the group being declared. 'Env' or 'EnvGroup' found: Env('dev1')"
    assert serr == ''  # TODO empty error message


_eg_name_used_expected_ex = """Name 'g_dev' is already used by group: EnvGroup('g_dev') {
   Env('dev1')
}"""

def test_env_name_used():
    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        myef1.Env('dev1')
        myef1.Env('dev1')

    assert str(exinfo.value) == "Name 'dev1' is already used by env: Env('dev1')"

    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        mydev1 = myef1.Env('dev1')
        myef1.EnvGroup('g_dev', mydev1)
        mydev1 = myef1.Env('g_dev')

    print(str(exinfo.value))
    assert str(exinfo.value) == _eg_name_used_expected_ex


def test_group_name_used():
    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        myef1.Env('dev1')
        myef1.EnvGroup('dev1')

    assert str(exinfo.value) == "Name 'dev1' is already used by env: Env('dev1')"

    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        mydev1 = myef1.Env('dev1')
        myef1.EnvGroup('g_dev', mydev1)
        myef1.EnvGroup('g_dev', mydev1)

    assert str(exinfo.value) == _eg_name_used_expected_ex


def test_repeated_nested_env_member_reversed():
    myef = EnvFactory()
    ii1 = myef.Env('ii1')
    ii2 = myef.EnvGroup('ii2', ii1)
    ii3 = myef.EnvGroup('ii3', ii2, ii1)

    assert ii1 in ii3
    assert ii2 in ii3


def test_repeated_nested_group_member():
    myef = EnvFactory()
    jj1 = myef.Env('jj1')
    jj2 = myef.EnvGroup('jj2', jj1)
    jj3 = myef.EnvGroup('jj3', jj2)
    jj4 = myef.EnvGroup('jj4', jj3, jj2)

    assert jj1 in jj4
    assert jj2 in jj4
    assert jj3 in jj4


def test_repeated_nested_group_member_reversed():
    myef = EnvFactory()
    jj1 = myef.Env('jj1')
    jj2 = myef.EnvGroup('jj2', jj1)
    jj3 = myef.EnvGroup('jj3', jj2)
    jj4 = myef.EnvGroup('jj4', jj2, jj3)

    assert jj1 in jj4
    assert jj2 in jj4
    assert jj3 in jj4


def test_no_groups(capsys):
    myef = EnvFactory()
    mydev1 = myef.Env('dev1')
    myef._mc_calc_env_group_order()


test_json_json = """{
    "type": "<class 'multiconf.envs.EnvGroup'>",
    "name": "jj4",
    "bit": 16,
    "mask": "0b0000000000011110",
    "members": [
        {
            "type": "<class 'multiconf.envs.EnvGroup'>",
            "name": "jj2",
            "bit": 4,
            "mask": "0b0000000000000110",
            "members": [
                {
                    "type": "<class 'multiconf.envs.Env'>",
                    "name": "jj1",
                    "bit": 2,
                    "mask": "0b0000000000000010",
                    "members": []
                }
            ]
        },
        {
            "type": "<class 'multiconf.envs.EnvGroup'>",
            "name": "jj3",
            "bit": 8,
            "mask": "0b0000000000001110",
            "members": [
                {
                    "type": "<class 'multiconf.envs.EnvGroup'>",
                    "name": "jj2",
                    "bit": 4,
                    "mask": "0b0000000000000110",
                    "members": [
                        {
                            "type": "<class 'multiconf.envs.Env'>",
                            "name": "jj1",
                            "bit": 2,
                            "mask": "0b0000000000000010",
                            "members": []
                        }
                    ]
                }
            ]
        }
    ]
}"""

def test_json():
    myef = EnvFactory()
    jj1 = myef.Env('jj1')
    jj2 = myef.EnvGroup('jj2', jj1)
    jj3 = myef.EnvGroup('jj3', jj2)
    jj4 = myef.EnvGroup('jj4', jj2, jj3)

    print(jj4.json())
    assert jj4.json() == test_json_json
