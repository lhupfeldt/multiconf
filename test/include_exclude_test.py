# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno
from .utils.compare_json import compare_json

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import required, repeat, nested_repeatables

from ..envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
dev2ct = ef.Env('dev2ct')
dev2st = ef.Env('dev2st')
g_dev = ef.EnvGroup('g_dev', dev2ct, dev2st)
pp = ef.Env('pp')
prod = ef.Env('prod')


@required('anattr, anotherattr')
class item(ConfigItem):
    pass


_include_exclude_for_configitem_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": 1,
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude_test.item'>": true
}"""

def test_include_for_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_include=[dev2ct, pp]) as it:
                it.setattr('anattr', pp=1, g_dev=2)
                it.setattr('anotherattr', dev2ct=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev2ct)
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


def test_include_missing_for_configitem(capsys):
    def conf(env, errorline):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_include=[dev2ct, pp]) as it:
                errorline.append(lineno() + 1)
                it.setattr('anattr', g_dev=2)
                it.setattr('anotherattr', dev2ct=1, pp=2)
        return cr

    errorline = []
    with raises(ConfigException) as exinfo:
        conf(prod, errorline)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], "Attribute: 'anattr' did not receive a value for env Env('pp')")
    assert "There were 1 errors when defining attribute 'anattr' on object" in exinfo.value.message


def test_exclude_for_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_exclude=[dev2st, prod]) as it:
                it.setattr('anattr', pp=1, g_dev=2)
                it.setattr('anotherattr', dev2ct=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev2ct)
    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 1


@required('anattr, anotherattr')
@repeat()
class ritem(ConfigItem):
    pass


@nested_repeatables('ritems')
class root(ConfigRoot):
    pass


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

def test_include_for_configitem_repeatable():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_include=[dev2ct, pp]) as it:
                it.setattr('anattr', pp=1, g_dev=2)
                it.setattr('anotherattr', dev2ct=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert cr.ritems == {}
    compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = conf(dev2ct)
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_exclude_for_configitem_repeatable():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_exclude=[dev2st, prod]) as it:
                it.setattr('anattr', pp=1, g_dev=2)
                it.setattr('anotherattr', dev2ct=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert cr.ritems == {}
    compare_json(cr, _include_exclude_for_configitem_repeatable_expected_json, test_excluded=True)

    cr = conf(dev2ct)
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].anotherattr == 1


def test_exclude_for_nested_configitem():
    def conf(env):
        with ConfigRoot(env, ef) as cr:
            cr.a = 1
            with item(mc_exclude=[dev2st, prod]) as it1:
                it1.setattr('anattr', pp=1, g_dev=2)
                it1.setattr('anotherattr', dev2ct=1, pp=2)
                with item() as it2:
                    it2.setattr('anattr', pp=1, g_dev=2)
                    it2.setattr('anotherattr', dev2ct=1, pp=2)
        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev2ct)
    assert cr.item.item.anattr == 2
    assert cr.item.item.anotherattr == 1


def test_exclude_for_repeatable_nested_configitem():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_exclude=[dev2st, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev=2)
                rit.setattr('anotherattr', dev2ct=1, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev=2)
                    it1.setattr('anotherattr', dev2ct=1, pp=2)
                    with item() as it2:
                        it2.setattr('anattr', pp=1, g_dev=2)
                        it2.setattr('anotherattr', dev2ct=1, pp=2)

            with ritem(id='b', mc_exclude=[dev2ct]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev=2)
                rit.setattr('anotherattr', dev2ct=1, dev2st=3, pp=2, prod=44)
                with item() as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev=2)
                    it1.setattr('anotherattr', dev2ct=1, dev2st=1, pp=2, prod=43)

            with ritem(id='c', mc_exclude=[dev2st, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev=2)
                rit.setattr('anotherattr', dev2ct=1, pp=2)
                with item() as it1:
                    it1.setattr('anattr', pp=1, g_dev=2)
                    it1.setattr('anotherattr', dev2ct=1, pp=2)

        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33
    assert 'c' not in cr.ritems
    assert len(cr.ritems) == 1

    cr = conf(dev2ct)
    assert cr.a == 1
    assert 'a' in cr.ritems
    assert 'b' not in cr.ritems
    assert 'c' in cr.ritems
    assert cr.ritems['c'].anattr == 2
    assert cr.ritems['c'].item.anattr == 2
    assert cr.ritems['c'].item.anotherattr == 1
    assert len(cr.ritems) == 2


def test_exclude_for_repeatable_nested_excludes_configitem():
    def conf(env):
        with root(env, ef) as cr:
            cr.a = 1
            with ritem(id='a', mc_exclude=[dev2st, prod]) as rit:
                rit.setattr('anattr', pp=1, g_dev=2)
                rit.setattr('anotherattr', dev2ct=1, pp=2)
                with item(mc_exclude=[pp]) as it1:
                    it1.setattr('anattr', pp=1, g_dev=2)
                    it1.setattr('anotherattr', dev2ct=1, pp=2)
                    with item(mc_exclude=[dev2st]) as it2:
                        it2.setattr('anattr', pp=1, g_dev=2)
                        it2.setattr('anotherattr', dev2ct=1, pp=2)

            with ritem(id='b', mc_exclude=[dev2ct]) as rit:
                rit.setattr('anattr', prod=31, pp=1, g_dev=2)
                rit.setattr('anotherattr', dev2ct=1, dev2st=3, pp=2, prod=44)
                with item(mc_exclude=[pp]) as it1:
                    it1.setattr('anattr', prod=33, pp=1, g_dev=2)
                    it1.setattr('anotherattr', dev2ct=1, dev2st=1, pp=2, prod=43)

        return cr

    cr = conf(prod)
    assert cr.a == 1
    assert len(cr.ritems) == 1

    assert 'a' not in cr.ritems
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 31
    assert cr.ritems['b'].item.anattr == 33

    cr = conf(dev2ct)
    assert cr.a == 1
    assert len(cr.ritems) == 1

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 2
    assert cr.ritems['a'].item.item.anattr == 2
    assert 'b' not in cr.ritems

    cr = conf(pp)
    assert cr.a == 1
    assert len(cr.ritems) == 2

    assert 'a' in cr.ritems
    assert cr.ritems['a'].anattr == 1
    assert not cr.ritems['a'].item
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 1
    assert not cr.ritems['b'].item

    cr = conf(dev2st)
    assert cr.a == 1
    assert len(cr.ritems) == 1

    assert 'a' not in cr.ritems
    with raises(KeyError):
        _ = cr.ritems['a']
    assert 'b' in cr.ritems
    assert cr.ritems['b'].anattr == 2
    assert cr.ritems['b'].anotherattr == 3
    assert cr.ritems['b'].item.anattr == 2
    assert cr.ritems['b'].item.anotherattr == 1
