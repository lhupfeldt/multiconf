#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .utils import config_error, replace_ids

from .. import ConfigRoot, ConfigItem
from ..decorators import  required, required_if, named_as, optional

from ..envs import EnvFactory

ef = EnvFactory()

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

dev2ct = ef.Env('dev2ct')
dev2st = ef.Env('dev2st')
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3ct')
dev3st = ef.Env('dev3st')
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)

_g_expected = """{
    "__class__": "root #as: 'project', id: 0000", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "name": "abc"
}"""


def test_required_attributes_for_configroot():
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    with root(prod, [prod]) as cr:
        cr.setattr('anattr',prod=1)
        cr.setattr('anotherattr', prod=2)
    assert cr.anattr == 1
    assert cr.anotherattr == 2


def test_required_attributes_for_configitem():
    class root(ConfigRoot):
        pass

    @required('a, b')
    class item(ConfigItem):
        pass

    with root(prod, [prod]) as cr:
        with item() as ii:
            ii.setattr('a', prod=1)
            ii.setattr('b', prod=2)

    assert cr.item.a == 1
    assert cr.item.b == 2


def test_required_attributes_accept_override_of_single_property():
    class root(ConfigRoot):
        pass

    @required('a, b')
    class item(ConfigItem):
        def __init__(self, a, b):
            super(item, self).__init__(a=a, b=b)

    with root(prod, [prod]) as cr:
        with item(a=1, b=1) as ii:
            ii.setattr('b', prod=2)

    assert cr.item.a == 1
    assert cr.item.b == 2


def test_required_if_attributes_condition_true_prod_and_condition_unset_dev2ct():
    @required_if('a', 'b, c')
    class root(ConfigRoot):
        pass

    with root(prod, [prod, dev2ct]) as cr:
        cr.setattr('a', prod=10)
        cr.setattr('b', prod=20)
        cr.setattr('c', prod=30)

    assert cr.a == 10
    assert cr.b == 20
    assert cr.c == 30

    # Test iteritems
    expected_keys = ['a', 'b', 'c']
    index = 0
    for key, val in cr.iteritems():
        assert key == expected_keys[index]
        assert val == (index + 1) * 10
        index += 1


def test_required_if_attributes_condition_false():
    @required_if('a', 'b, c')
    class root(ConfigRoot):
        pass

    with root(prod, [prod]) as cr:
        cr.setattr('a', prod=0)
        cr.setattr('b', prod=10)

    assert cr.a == 0
    assert cr.b == 10

    # Test iteritems
    expected_keys = ['a', 'b']
    index = 0
    for key, val in cr.iteritems():
        assert key == expected_keys[index]
        assert val == index * 10
        index += 1


def test_optional_attribute():
    @optional('a')
    class root(ConfigRoot):
        pass

    with root(prod, [prod, dev2ct]) as cr:
        cr.setattr('a', dev2ct=18)
    assert "no-exception" == "no-exception"

    with root(prod, [prod, dev2ct]) as cr:
        cr.setattr('a', prod=17)
    assert cr.a == 17


def test_named_as():
    @named_as('project')
    class root(ConfigRoot):
        pass

    with root(prod, [prod, dev2ct], name='abc') as proj:
        pass
    assert replace_ids(repr(proj), named_as=False) == _g_expected


def test_required_attributes_inherited_ok():
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    @required('someattr2, someotherattr2')
    class root2(root):
        pass

    with root2(prod, [prod]) as cr:
        cr.setattr('anattr', prod=1)
        cr.setattr('anotherattr', prod=2)
        cr.setattr('someattr2', prod=3)
        cr.setattr('someotherattr2', prod=4)
    assert cr.anattr == 1
    assert cr.anotherattr == 2
    assert cr.someattr2 == 3
    assert cr.someotherattr2 == 4
