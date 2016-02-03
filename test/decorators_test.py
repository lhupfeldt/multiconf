# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .utils.utils import config_error, replace_ids

from .. import ConfigRoot, ConfigItem
from ..decorators import required, named_as, nested_repeatables

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


def test_required_attributes_for_configroot_as_str():
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
        cr.setattr('anattr', prod=1)
        cr.setattr('anotherattr', prod=2)
    assert cr.anattr == 1
    assert cr.anotherattr == 2


def test_required_attributes_for_configroot_as_args():
    @required('anattr', 'anotherattr')
    class root(ConfigRoot):
        pass

    with root(prod1, ef1_prod) as cr:
        cr.setattr('anattr', prod=1)
        cr.setattr('anotherattr', prod=2)
    assert cr.anattr == 1
    assert cr.anotherattr == 2
    

def test_required_attributes_for_configitem_as_str():
    class root(ConfigRoot):
        pass

    @required('a, b')
    class item(ConfigItem):
        pass

    with root(prod1, ef1_prod) as cr:
        with item() as ii:
            ii.setattr('a', prod=1)
            ii.setattr('b', prod=2)

    assert cr.item.a == 1
    assert cr.item.b == 2


def test_required_attributes_for_configitem_as_args():
    class root(ConfigRoot):
        pass

    @required('a', 'b')
    class item(ConfigItem):
        pass

    with root(prod1, ef1_prod) as cr:
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
            super(item, self).__init__()
            self.a = a
            self.b = b

    with root(prod1, ef1_prod) as cr:
        with item(a=1, b=1) as ii:
            ii.setattr('b', prod=2)

    assert cr.item.a == 1
    assert cr.item.b == 2


def test_named_as():
    @named_as('project')
    class root(ConfigRoot):
        pass

    with root(prod2, ef2_prod_dev2ct) as proj:
        proj.name = 'abc'
    assert replace_ids(repr(proj), named_as=False) == _g_expected


def test_required_attributes_inherited_ok():
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    @required('someattr2, someotherattr2')
    class root2(root):
        pass

    with root2(prod1, ef1_prod) as cr:
        cr.setattr('anattr', prod=1)
        cr.setattr('anotherattr', prod=2)
        cr.setattr('someattr2', prod=3)
        cr.setattr('someotherattr2', prod=4)
    assert cr.anattr == 1
    assert cr.anotherattr == 2
    assert cr.someattr2 == 3
    assert cr.someotherattr2 == 4


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
