# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .. import ConfigRoot, ConfigItem
from ..decorators import named_as, nested_repeatables

from .utils.utils import config_error, replace_ids
from .utils.tstclasses import RootWithName

from ..envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_dev2ct = EnvFactory()
pp2 = ef2_prod_dev2ct.Env('dev2ct')
prod2 = ef2_prod_dev2ct.Env('prod')


_g_expected = """{
    "__class__": "root #as: 'project', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "name": "abc"
}"""

def test_named_as():
    @named_as('project')
    class root(RootWithName):
        pass

    with root(prod2, ef2_prod_dev2ct) as proj:
        proj.name = 'abc'
    assert replace_ids(repr(proj), named_as=False) == _g_expected


def test_nested_repeatables_attributes_for_configroot_as_str():
    @nested_repeatables('ritm1, ritm2')
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
        cr
    assert cr.ritm1 == {}
    assert cr.ritm2 == {}


def test_nested_repeatables_attributes_for_configroot_as_args():
    @nested_repeatables('ritm1', 'ritm2')
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
        cr
    assert cr.ritm1 == {}
    assert cr.ritm2 == {}
