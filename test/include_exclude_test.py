# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .utils.utils import config_error
from .utils.compare_json import compare_json

from .. import ConfigRoot, ConfigItem
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
