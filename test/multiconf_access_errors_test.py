# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, replace_ids
from .utils.utils import py3_lcls

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import nested_repeatables, named_as, repeat
from ..envs import EnvFactory

ef1_prod = EnvFactory()

prod = ef1_prod.Env('prod')

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_access_undefined_attribute_expected_repr = """{
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    }
}, object of type: <class 'multiconf.multiconf.ConfigRoot'> has no attribute 'b'"""

def test_access_undefined_attribute():
    with ConfigRoot(prod, ef1_prod) as cr:
        pass

    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(str(exinfo.value), named_as=False) == _access_undefined_attribute_expected_repr


_t2_expected_repr = """{
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "bs": 4
}, object of type: <class 'multiconf.multiconf.ConfigRoot'> has no attribute 'b', but found attribute 'bs'"""

def test_access_undefined_attribute_but_has_repeatable_attribute_with_attribute_name_plus_s():
    with ConfigRoot(prod, ef1_prod) as cr:
        cr.setattr('bs', prod=4)

    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(str(exinfo.value), named_as=False) == _t2_expected_repr


_find_contained_in_named_as_not_found_expected = """Searching from: <class 'multiconf.test.multiconf_access_errors_test%(py3_lcls)s.Y'>: Could not find a parent container named as: 'notthere' in hieracy with names: ['someitems', 'x', 'someitems', 'x', 'root']"""

def test_find_contained_in_named_as_not_found():
    @named_as('someitems')
    @nested_repeatables('someitems')
    @repeat()
    class NestedRepeatable(ConfigItem):
        pass

    @named_as('x')
    @nested_repeatables('someitems')
    class X(ConfigItem):
        pass

    @named_as('y')
    class Y(ConfigItem):
        pass

    @nested_repeatables('someitems')
    class root(ConfigRoot):
        pass

    with root(prod, ef1_prod, a=0) as cr:
        NestedRepeatable()
        with X() as ci:
            ci.setattr('a', prod=0)
            NestedRepeatable(id='a')
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='c')
                with X() as ci:
                    ci.setattr('a', prod=1)
                    with NestedRepeatable(id='d') as ci:
                        ci.setattr('a', prod=2)
                        with Y() as ci:
                            ci.setattr('a', prod=3)

    with raises(ConfigException) as exinfo:
        cr.x.someitems['b'].x.someitems['d'].y.find_contained_in(named_as='notthere').a

    assert replace_ids(str(exinfo.value)) == _find_contained_in_named_as_not_found_expected % dict(py3_lcls=py3_lcls())


_find_attribute_with_attribute_name_not_found = """Searching from: <class 'multiconf.test.multiconf_access_errors_test%(py3_lcls)s.X'>: Could not find an attribute named: 'e' in hieracy with names: ['x', 'someitems', 'x', 'someitems', 'x', 'root']"""

def test_find_attribute_with_attribute_name_not_found():
    @named_as('someitems')
    @nested_repeatables('someitems')
    @repeat()
    class NestedRepeatable(ConfigItem):
        pass

    @named_as('x')
    @nested_repeatables('someitems')
    class X(ConfigItem):
        pass

    @nested_repeatables('someitems')
    class root(ConfigRoot):
        pass

    with root(prod, ef1_prod, a=0, q=17) as cr:
        NestedRepeatable()
        with X() as ci:
            ci.setattr('a', prod=0)
            NestedRepeatable(id='a', a=9)
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='c', a=7)
                with X() as ci:
                    ci.setattr('b', prod=1)
                    with NestedRepeatable(id='d') as ci:
                        ci.setattr('a', prod=2)
                        with X() as ci:
                            ci.setattr('a', prod=3)

    with raises(ConfigException) as exinfo:
        assert cr.x.someitems['b'].x.someitems['d'].x.find_attribute('e') == 3

    assert replace_ids(str(exinfo.value)) == _find_attribute_with_attribute_name_not_found % dict(py3_lcls=py3_lcls())


# TODO
#def test_error_in_property_method_implementation(self):
#    class root(ConfigRoot):
#        pass
#
#    @named_as('x')
#    class X(ConfigItem):
#        @property
#        def method(self):
#            # Cheat pylint by getting string from dict
#            a = {1:""}
#            return a[1].nosuchprop
#
#    with root(prod, ef1_prod) as cr:
#        X()
#
#    with raises(ConfigException) as exinfo:
#        a = cr.x.method
#
#    assert str(exinfo.value) == ""
