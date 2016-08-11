# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, assert_lines_in
from .utils.compare_json import compare_json

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigException, MC_REQUIRED
from ..decorators import named_as, nested_repeatables, required
from ..config_errors import ConfigAttributeError

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


@nested_repeatables('ritems')
class item(ConfigItem):
    def __init__(self, mc_include=None, mc_exclude=None):
        super(item, self).__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anattr = MC_REQUIRED
        self.anotherattr = None
        self.x = None
        self.y = None


class anitem(ConfigItem):
    xx = 1


class ritem(RepeatableConfigItem):
    def __init__(self, name, mc_include=None, mc_exclude=None):
        super(ritem, self).__init__(mc_key=name, mc_include=mc_include, mc_exclude=mc_exclude)
        self.name = name
        self.anattr = MC_REQUIRED
        self.anotherattr = MC_REQUIRED


class root(ConfigRoot):
    def __init__(self, selected_env, env_factory):
        super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)
        self.x = None
        self.y = None
        self.z = None


@named_as('ritems')
@required('anitem')
class decorated_ritem(ritem):
    pass
        

@named_as('root')
@nested_repeatables('ritems', 'decorated_ritems')
class decorated_root(ConfigRoot):
    def __init__(self, selected_env, env_factory):
        super(decorated_root, self).__init__(selected_env=selected_env, env_factory=env_factory)
        self.a = None
        self.x = None


_include_exclude_for_configitem_expected_json = """{
    "__class__": "root",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "x": null,
    "z": null,
    "y": false,
    "y #Excluded: <class 'multiconf.test.include_exclude_ignore_refs_test.item'>": true,
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude_ignore_refs_test.item'>": true
}"""


def test_exclude_refs_for_nested_configitem():
    def conf(env):
        with root(env, ef) as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)
            cr.y = it1.item

        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)
    assert not cr.y

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.y == cr.item.item


def test_exclude_refs_for_nested_configitem_with_mc_required():
    def conf(env):
        with root(env, ef) as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)

            cr.x = it1.anattr  # This is illegal if it1.anattr has not been set because it1 was excluded
            cr.y = it1.item
            cr.z = it1.item.anattr

        return cr

    with raises(AttributeError) as exinfo:
        conf(prod)
    assert "Attribute 'anattr' MC_REQUIRED (on excluded object) is undefined for current env Env('prod')" in str(exinfo.value)

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.x == cr.item.anattr
    assert cr.y == cr.item.item
    assert cr.z == cr.item.item.anattr


def test_exclude_refs_for_repeatable_nested_configitem():
    def conf(env):
        with decorated_root(env, ef) as cr:
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


def test_exclude_refs_for_repeatable_nested_configitem_required_items():
    def conf(env):
        with decorated_root(env, ef) as cr:
            cr.a = 1
            with decorated_ritem(name='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)
                anitem()

                with item(mc_exclude=[dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with decorated_ritem(name='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)
                        anitem()

                    with decorated_ritem(name='b', mc_exclude=[dev1]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)
                        anitem()

                    it1.x = it1.ritems['a']
                    it1.y = it1.ritems['b'].anattr

            cr.x = rit.item.ritems['a'].anotherattr

            with decorated_ritem(name='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                anitem()

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

        return cr

    # TODO validate more of 'anitem'
    cr = conf(prod)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33
    assert cr.ritems['b'].anitem.xx == 1

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
        with root(env, ef) as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)

                cr.y = it1.item

        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)
    assert not cr.y

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.y == cr.item.item


def test_exclude_refs_for_nested_configitem_before_exit_with_mc_required_refs():
    def conf(env):
        with root(env, ef) as cr:
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

    with raises(AttributeError) as exinfo:
        conf(prod)
        # TODO

    cr = conf(dev1)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.x == cr.item.anattr
    assert cr.y == cr.item.item
    assert cr.z == cr.item.item.anattr


def test_exclude_refs_for_repeatable_nested_configitem_before_exit():
    def conf(env):
        with decorated_root(env, ef) as cr:
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
        with decorated_root(env, ef) as cr:
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
    with raises(AttributeError):
        _ = cr.x.a
        # TODO text
    with raises(TypeError):
        _ = cr.x['q']
        # TODO text

    cr = conf(dev3)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1
