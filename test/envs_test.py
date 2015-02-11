# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises
from .utils.utils import replace_user_file_line_msg

from ..envs import EnvFactory, EnvException


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
all_envs = groups_only + envs_only

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
    assert g_dev_tst != None
    assert g_prod != 1
    assert dev1 != None
    assert prod != "Hello"
    assert not prod == "Hello"

    # Compare other types to self
    assert None != g_dev_tst
    assert 1 != g_prod
    assert None != dev1
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


def test_iterating_groups_and_envs():
    envs = []
    for env in valid_envs.all:
        envs.append(env)
    assert envs == all_envs


def test_as_key():
    envs = {}
    for env in valid_envs.all:
        envs[env] = True
    for env in valid_envs.all:
        assert envs[env] == True


def test_env_from_name():
    assert ef.env("dev1").name == "dev1"

    with raises(EnvException) as exinfo:
        ef.env("g_dev_tst")
    assert exinfo.value.message == "No such Env: 'g_dev_tst'"

    with raises(EnvException) as exinfo:
        ef.env("no-way")
    assert exinfo.value.message == "No such Env: 'no-way'"


def test_env_or_group_from_name():
    assert ef.env_or_group_from_name("dev1").name == "dev1"
    assert ef.env_or_group_from_name("g_dev_tst").name == "g_dev_tst"

    with raises(EnvException) as exinfo:
        ef.env_or_group_from_name("no-way")
    assert exinfo.value.message == "No such Env or EnvGroup: 'no-way'"


def test_env_or_group_from_bit():
    ef._mc_init_and_default_groups()  # pylint: disable=protected-access

    assert ef.env_or_group_from_bit(0b0000000000000010).name == "dev1"
    assert ef.env_or_group_from_bit(prod.mask) == prod
    assert ef.env_or_group_from_bit(0b0000001000000000) == prod
    assert ef.env_or_group_from_bit(0b0000010000000000) == g_prod
    assert ef.env_or_group_from_bit(0b0001000000000000).name == "default"
    assert ef.env_or_group_from_bit(0b0010000000000000).name == "__init__"

    with raises(EnvException) as exinfo:
        ef.env_or_group_from_bit(0b1000000000000000)
    assert exinfo.value.message == "No Env or EnvGroup with bit 0b1000000000000000"


def test_envs_from_mask():
    ef._mc_init_and_default_groups()  # pylint: disable=protected-access

    found_envs = []
    for env in ef.envs_from_mask(0b100010100):
        found_envs.append(env)
    assert found_envs == [dev2, tst1, pp]


def test_eg_bits():
    assert g_dev_tst.eg_bits == [1, 2 ,3, 4, 5, 6, 7]
    assert g_prod.eg_bits == [8, 9, 10]


def test_env_bits():
    assert g_dev_tst.env_bits == [1, 2, 4, 5]
    assert g_prod.env_bits == [8, 9]


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
        myef._mc_init_and_default_groups()  # pylint: disable=protected-access
        myef.EnvGroup('g_dev12', mydev1)

    _sout, serr = capsys.readouterr()
    assert exinfo.value.message == "EnvFactory is already in use. No more groups may be added."
    assert replace_user_file_line_msg(serr) == ''  # TODO empty error message

    with raises(EnvException) as exinfo:
        myef = EnvFactory()
        mydev1 = myef.Env('dev1')
        myef._mc_init_and_default_groups()  # pylint: disable=protected-access
        myef.Env('dev2')

    _sout, serr = capsys.readouterr()
    assert exinfo.value.message == "EnvFactory is already in use. No more envs may be added."
    assert replace_user_file_line_msg(serr) == ''  # TODO empty error message


def test_group_members_not_same_factory(capsys):
    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        mydev1 = myef1.Env('dev1')
        myef2 = EnvFactory()
        mydev2 = myef1.Env('dev2')
        myef2.EnvGroup('g_dev12', mydev1, mydev2)

    _sout, serr = capsys.readouterr()
    assert exinfo.value.message == "EnvGroup: The group members must be from the same 'env_factory' as the group being declared. 'Env' or 'EnvGroup' found: Env('dev1')"
    assert replace_user_file_line_msg(serr) == ''  # TODO empty error message


_eg_name_used_expected_ex = """Name 'g_dev' is already used by group: EnvGroup('g_dev') {
     Env('dev1')
}"""

def test_env_name_used():
    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        myef1.Env('dev1')
        myef1.Env('dev1')

    assert exinfo.value.message == "Name 'dev1' is already used by env: Env('dev1')"

    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        mydev1 = myef1.Env('dev1')
        myef1.EnvGroup('g_dev', mydev1)
        mydev1 = myef1.Env('g_dev')

    print exinfo.value.message
    assert exinfo.value.message == _eg_name_used_expected_ex


def test_group_name_used():
    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        myef1.Env('dev1')
        myef1.EnvGroup('dev1')

    assert exinfo.value.message == "Name 'dev1' is already used by env: Env('dev1')"

    with raises(EnvException) as exinfo:
        myef1 = EnvFactory()
        mydev1 = myef1.Env('dev1')
        myef1.EnvGroup('g_dev', mydev1)
        myef1.EnvGroup('g_dev', mydev1)

    assert exinfo.value.message == _eg_name_used_expected_ex


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

    print jj4.json()
    assert jj4.json() == test_json_json
