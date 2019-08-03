# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises, xfail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException, ConfigExcludedAttributeError, ConfigExcludedKeyError, MC_REQUIRED
from multiconf.decorators import named_as, nested_repeatables, required
from multiconf.envs import EnvFactory

from .utils.utils import config_error
from .utils.compare_json import compare_json

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
        super().__init__(mc_include=mc_include, mc_exclude=mc_exclude)
        self.anattr = MC_REQUIRED
        self.anotherattr = None
        self.x = None
        self.y = None


class anitem(ConfigItem):
    xx = 1


class ritem(RepeatableConfigItem):
    def __init__(self, mc_key, mc_include=None, mc_exclude=None):
        super().__init__(mc_key=mc_key, mc_include=mc_include, mc_exclude=mc_exclude)
        self.name = mc_key
        self.anattr = MC_REQUIRED
        self.anotherattr = MC_REQUIRED


class root(ConfigItem):
    def __init__(self):
        super().__init__()
        self.x = None
        self.y = None
        self.z = None


@named_as('ritems')
@required('anitem')
class decorated_ritem(ritem):
    pass


@named_as('root')
@nested_repeatables('ritems', 'decorated_ritems')
class decorated_root(ConfigItem):
    def __init__(self):
        super().__init__()
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
    "y": "#ref later excluded, id: 0000",
    "z": null,
    "item": false,
    "item #Excluded: <class 'test.include_exclude_ignore_refs_test.item'>": true
}"""

def test_exclude_refs_for_nested_configitem1():
    @mc_config(ef, load_now=True)
    def config(_):
        with root() as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)
            cr.y = it1.item

    cr = config(prod).root
    assert not cr.item
    assert compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)
    assert not cr.y

    cr = config(dev1).root
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.y == cr.item.item


def test_exclude_refs_for_nested_configitem_with_mc_required():
    @mc_config(ef, load_now=True)
    def conf(_):
        with root() as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)

    cr = conf(prod).root

    assert not cr.item

    with raises(AttributeError) as exinfo:
        cr.item.anattr  # This is illegal if it1.anattr has not been set because it1 was excluded
    exp = "Accessing attribute 'anattr' for Env('prod') on an excluded config item: Excluded: <class 'test.include_exclude_ignore_refs_test.item'>"
    assert exp in str(exinfo.value)

    # TODO: It would be nice it this would raise AttributeError as above as cr.item is excluded, but that would require a different implementation
    assert not cr.item.item

    with raises(AttributeError) as exinfo:
        cr.item.item.anattr
    exp = "Accessing attribute 'anattr' for Env('prod') on an excluded config item: Excluded: <class 'test.include_exclude_ignore_refs_test.item'>"
    assert exp in str(exinfo.value)

    cr = conf(dev1).root
    assert cr.item
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1
    assert cr.item.item
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1


def test_exclude_refs_for_multilevel_excluded_configitem():
    with raises(ConfigExcludedKeyError) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with decorated_root() as cr:
                with ritem(mc_key='a', mc_exclude=[dev2, prod]) as rit:
                    rit.setattr('anattr', pp=1, g_dev12_3=2)
                    rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)

                    with item(mc_exclude=[dev3]) as it1:
                        it1.setattr('anattr', pp=1, g_dev12_3=2)
                        it1.setattr('anotherattr', dev1=1, pp=2)

                        with ritem(mc_key='a') as it2:
                            it2.setattr('anattr', pp=1, g_dev12_3=2)
                            it2.setattr('anotherattr', dev1=1, pp=2)

                # This is invalid as all of rit, rit.item and rit.item.ritems are excluded
                cr.x = rit.item.ritems['a']

    got = str(exinfo.value)
    print(got)
    exp = "'a'. 'Excluded: <class 'test.include_exclude_ignore_refs_test.ritem'>' for Env('dev2')."
    print(exp)
    assert exp in got


def test_exclude_refs_for_repeatable_nested_configitem():
    @mc_config(ef, load_now=True)
    def config(_):
        with decorated_root() as cr:
            cr.a = 1
            with ritem(mc_key='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)

                with item(mc_exclude=[dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(mc_key='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(mc_key='b', mc_exclude=[dev1]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    it1.x = it1.ritems['a']

            with ritem(mc_key='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

    cr = config(prod).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = config(dev1).root
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

    cr = config(dev2).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert not cr.x

    with raises(AttributeError):
        _ = cr.x.a

    with raises(AttributeError):
        _ = cr.x.bbb

    cr = config(dev3).root
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1


def test_exclude_refs_for_repeatable_nested_configitem_required_items():
    @mc_config(ef, load_now=True)
    def config(_):
        with decorated_root() as cr:
            cr.a = 1
            with decorated_ritem(mc_key='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)
                anitem()

                with item(mc_exclude=[dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with decorated_ritem(mc_key='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)
                        anitem()

                    with decorated_ritem(mc_key='b', mc_exclude=[dev1]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)
                        anitem()

                    it1.x = it1.ritems['a']

            with decorated_ritem(mc_key='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)
                anitem()

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

    # TODO validate more of 'anitem'
    cr = config(prod).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33
    assert cr.ritems['b'].anitem.xx == 1

    cr = config(dev1).root
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

    cr = config(dev2).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert not cr.x
    with raises(AttributeError):
        _ = cr.x.a

    cr = config(dev3).root
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1


def test_exclude_refs_for_nested_configitem_before_exit_with_mc_required_refs():
    @mc_config(ef, load_now=True)
    def config(_):
        with root() as cr:
            with item(mc_exclude=[dev2, dev3, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev12_3=2)
                it1.setattr('anotherattr', dev1=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev12_3=2)
                    it2.setattr('anotherattr', dev1=1, pp=2)

                # This is actually at the wrong indentation level, meaning the assignment is never done for excluded envs
                # TODO, discover this ?
                xfail('TODO')
                cr.x = it1.anattr
                cr.y = it1.item
                cr.z = it1.item.anattr

    cr = config(prod).root
    with raises(AttributeError):
        _ = cr.item.item.anattr
    with raises(AttributeError):
        _ = cr.item.item.anotherattr

    assert cr.x is None
    assert cr.y is None
    assert cr.z is None

    cr = config(dev1).root
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1
    assert cr.x == cr.item.anattr
    assert cr.y == cr.item.item
    assert cr.z == cr.item.item.anattr


def test_exclude_refs_for_repeatable_nested_configitem_before_exit():
    xfail('TODO')
    @mc_config(ef, load_now=True)
    def config(_):
        with decorated_root() as cr:
            cr.a = 1
            with ritem(mc_key='a', mc_exclude=[dev2, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)

                with item(mc_exclude=[dev3]) as it1:
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(mc_key='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(mc_key='b', mc_exclude=[dev1]) as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                        it1.x = it1.ritems['a']
                        it1.y = it1.ritems['b'].anattr

                cr.x = rit.item.ritems['a'].anotherattr

            with ritem(mc_key='b', mc_exclude=[dev1, dev3]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

    cr = config(prod).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = config(dev1).root
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

    cr = config(dev2).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert not cr.x
    with raises(ConfigException):
        _ = cr.x.a
    with raises(ConfigException):
        _ = cr.x['q']

    cr = config(dev3).root
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1


def test_exclude_refs_for_repeatable_nested_configitem_before_exit_skip_block():
    @mc_config(ef, load_now=True)
    def config(_):
        with decorated_root() as cr:
            cr.a = 1
            with ritem(mc_key='a') as rit:
                rit.mc_select_envs(exclude=[dev2, prod])
                rit.setattr('anattr', pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, pp=2, dev3=117)

                with item() as it1:
                    it1.mc_select_envs(exclude=[dev3])
                    it1.setattr('anattr', pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(mc_key='a') as it2:
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                    with ritem(mc_key='b') as it2:
                        it2.mc_select_envs(exclude=[dev1])
                        it2.setattr('anattr', pp=1, g_dev12_3=2)
                        it2.setattr('anotherattr', dev1=1, pp=2)

                        it1.x = it1.ritems['a']
                        it1.y = it1.ritems['b'].anattr

                try:
                    # This is invalid as it will fail for 'dev3'
                    _ = rit.item.ritems['a'].anotherattr
                except ConfigExcludedKeyError:
                    assert cr.env == dev3

            with ritem(mc_key='b') as rit:
                rit.mc_select_envs(exclude=[dev1, dev3])
                rit.setattr('anattr', prod=31, pp=1, g_dev12_3=2)
                rit.setattr('anotherattr', dev1=1, dev2=3, pp=2, prod=44)

                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev12_3=2)
                    it1.setattr('anotherattr', dev1=1, dev2=1, pp=2, prod=43)

    cr = config(prod).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = config(dev1).root
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

    cr = config(dev2).root
    assert cr.a == 1
    assert 'a' not in cr.ritems
    with raises(AttributeError):
        _ = cr.x.a
        # TODO text
    with raises(TypeError):
        _ = cr.x['q']
        # TODO text

    cr = config(dev3).root
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert not cr.ritems['a'].item
    assert len(cr.ritems) == 1
