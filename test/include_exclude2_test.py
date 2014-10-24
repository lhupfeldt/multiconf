# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, assert_lines_in
from .utils.compare_json import compare_json

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import required, repeat, nested_repeatables

from ..envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
dev3 = ef.Env('dev3')
dev4 = ef.Env('dev4')
dev5 = ef.Env('dev5')
g_dev12 = ef.EnvGroup('g_dev12', dev1, dev2)
g_dev34 = ef.EnvGroup('g_dev23', dev3, dev4)
g_dev12_3 = ef.EnvGroup('g_dev12_3', g_dev12, dev3)
g_dev2_34 = ef.EnvGroup('g_dev2_34', dev2, g_dev34)
pp = ef.Env('pp')
prod = ef.Env('prod')
g_ppr = ef.EnvGroup('g_ppr', pp, prod)


@required('anattr')
class item(ConfigItem):
    pass


_include_exclude_for_configitem_expected_json = """{
    "__class__": "ConfigRoot",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "item": false,
    "item #Excluded: <class 'multiconf.test.include_exclude2_test.item'>": true
}"""


def test_exclude_include_overlapping_groups_resolved():
    def conf(env):
        """Covers exclude resolve branch"""
        with ConfigRoot(env, ef) as cr:
            with item(mc_include=[g_dev12, g_dev12_3, pp, dev2], mc_exclude=[g_dev34, g_dev2_34, dev3]) as it:
                it.setattr('anattr', pp=1, g_dev12_3=2)
                it.setattr('b', pp=1, dev2=0)
                it.setattr('anotherattr', default=111, dev5=7)
        return cr

    cr = conf(prod)
    assert not cr.item
    compare_json(cr, _include_exclude_for_configitem_expected_json, test_excluded=True)

    cr = conf(dev1)
    assert not cr.item

    cr = conf(dev2)
    assert cr.item
    assert cr.item.b == 0

    cr = conf(dev3)
    assert not cr.item

    cr = conf(pp)
    assert cr.item
    assert cr.item.anattr == 1
    assert cr.item.b == 1
    assert cr.item.anotherattr == 111
