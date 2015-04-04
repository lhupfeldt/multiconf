# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, assert_lines_in
from .utils.compare_json import compare_json

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigException
from ..decorators import required, nested_repeatables

from ..envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
dev3 = ef.Env('dev3')
g_dev12 = ef.EnvGroup('g_dev12', dev1, dev2)
g_dev23 = ef.EnvGroup('g_dev23', dev2, dev3)
g_dev13 = ef.EnvGroup('g_dev13', dev1, dev3)
g_dev12_3 = ef.EnvGroup('g_dev12_3', g_dev12, dev3)
pp = ef.Env('pp')
prod = ef.Env('prod')
g_ppr = ef.EnvGroup('g_ppr', pp, prod)


@required('anattr')
@nested_repeatables('ritems')
class item(ConfigItem):
    pass


@required('anattr')
class ritem(RepeatableConfigItem):
    def __init__(self, name, mc_exclude=None):
        super(ritem, self).__init__(mc_key=name, mc_exclude=mc_exclude)
        self.name = name


@nested_repeatables('ritems')
class root(ConfigRoot):
    pass


_include_exclude_for_configitem_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude_ignore_refs_test.item'>": true,
    "x": false,
    "x #Excluded: <class 'multiconf.test.include_exclude_ignore_refs_test.item'>": true,
    "y": false,
    "y #Excluded: <class 'multiconf.test.include_exclude_ignore_refs_test.item'>": true,
    "z": false,
    "z #Excluded: <class 'multiconf.test.include_exclude_ignore_refs_test.item'>": true
}"""


_include_exclude_for_configitem_repeatable_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "ritems": {},
    "a": 1
}"""


def test_exclude_refs_for_nested_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)
            cr.x = it1.anattr
            cr.y = it1.item
            cr.z = it1.item.anattr

        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)
    assert not cr.x
    assert not cr.y
    assert not cr.z

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.x == cr.item.anattr
    assert cr.y == cr.item.item
    assert cr.z == cr.item.item.anattr


def test_exclude_refs_for_repeatable_nested_configitem():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(name='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)

                with item(mc_exclude=[dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(name='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(name='b', mc_exclude=[dev1]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    it1.x = it1.ritems['a']
                    it1.y = it1.ritems['b'].anattr

            cr.x = rit.item.ritems['a'].anotherattr

            with ritem(name='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = conf(dev1)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1
    assert cr.ritems['a'].item.ritems['a'].anattr == 2
    assert cr.ritems['a'].item.ritems['a'].anotherattr == 1
    with raises(KeyError):
        _ = cr.ritems['a'].item.ritems['b']
    assert len(cr.ritems) == 1

    cr = conf(dev2)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert not cr.x
    with raises(ConfigException):
        _ = cr.x.a
    with raises(ConfigException):
        _ = cr.x['q']

    cr = conf(dev3)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1


def test_exclude_refs_for_nested_configitem_before_exit():
    """Test that en excluded item ignores atribute references before it's with block scope is exited"""
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)
                cr.x = it1.anattr
                cr.y = it1.item
                cr.z = it1.item.anattr

        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)
    assert not cr.x
    assert not cr.y
    assert not cr.z

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.x == cr.item.anattr
    assert cr.y == cr.item.item
    assert cr.z == cr.item.item.anattr


def test_exclude_refs_for_repeatable_nested_configitem_before_exit():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(name='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)

                with item(mc_exclude=[dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(name='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(name='b', mc_exclude=[dev1]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                        it1.x = it1.ritems['a']
                        it1.y = it1.ritems['b'].anattr

                cr.x = rit.item.ritems['a'].anotherattr

            with ritem(name='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = conf(dev1)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1
    assert cr.ritems['a'].item.ritems['a'].anattr == 2
    assert cr.ritems['a'].item.ritems['a'].anotherattr == 1
    with raises(KeyError):
        _ = cr.ritems['a'].item.ritems['b']
    assert len(cr.ritems) == 1

    cr = conf(dev2)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert not cr.x
    with raises(ConfigException):
        _ = cr.x.a
    with raises(ConfigException):
        _ = cr.x['q']

    cr = conf(dev3)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1


def test_exclude_refs_for_repeatable_nested_configitem_before_exit_skip_block():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(name='a') as rit:
                rit.mc_select_envs(exclude=[dev2, prod])
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)

                with item() as it1:
                    it1.mc_select_envs(exclude=[dev3])
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(name='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(name='b') as it2:
                        it2.mc_select_envs(exclude=[dev1])
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                        it1.x = it1.ritems['a']
                        it1.y = it1.ritems['b'].anattr

                cr.x = rit.item.ritems['a'].anotherattr

            with ritem(name='b') as rit:
                rit.mc_select_envs(exclude=[dev1, dev3])
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = conf(dev1)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1
    assert cr.ritems['a'].item.ritems['a'].anattr == 2
    assert cr.ritems['a'].item.ritems['a'].anotherattr == 1
    with raises(KeyError):
        _ = cr.ritems['a'].item.ritems['b']
    assert len(cr.ritems) == 1

    cr = conf(dev2)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert not hasattr(cr, 'x')
    with raises(AttributeError):
        _ = cr.x.a
    with raises(AttributeError):
        _ = cr.x['q']

    cr = conf(dev3)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1
