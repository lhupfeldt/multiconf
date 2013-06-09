#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import nested_repeatables, named_as, repeat
from ..envs import EnvFactory

ef = EnvFactory()

prod = ef.Env('prod')

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_test_access_undefined_attribute_expected_repr = """{
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }
} has no attribute 'b'"""

def test_access_undefined_attribute():
    with ConfigRoot(prod, [prod]) as cr:
        pass

    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(exinfo.value.message, named_as=False) == _test_access_undefined_attribute_expected_repr


_t2_expected_repr = """{
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "bs": 4
} has no attribute 'b', but found attribute 'bs'"""

def test_access_undefined_attribute_but_has_repeatable_attribute_with_attribute_name_plus_s():
    with ConfigRoot(prod, [prod]) as cr:
        cr.setattr('bs', prod=4)

    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(exinfo.value.message, named_as=False) == _t2_expected_repr


_find_contained_in_named_as_not_found_expected = """Searching from: {
    "__class__": "Y #as: 'xxxx', id: 0000", 
    "a": 3
}: Could not find a parent container named as: 'notthere' in hieracy with names: ['someitems', 'x', 'someitems', 'x', 'root']"""

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

    with root(prod, [prod], a=0) as cr:
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
    
    assert replace_ids(exinfo.value.message) == _find_contained_in_named_as_not_found_expected


_find_attribute_with_attribute_name_not_found = """Searching from: {
    "__class__": "X #as: 'xxxx', id: 0000", 
    "someitems": {}, 
    "a": 3
}: Could not find an attribute named: 'e' in hieracy with names: ['x', 'someitems', 'x', 'someitems', 'x', 'root']"""

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

    with root(prod, [prod], a=0, q=17) as cr:
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
    
    assert replace_ids(exinfo.value.message) == _find_attribute_with_attribute_name_not_found


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
#    with root(prod, [prod]) as cr:
#        X()
#                
#    with raises(ConfigException) as exinfo:
#        a = cr.x.method
#
#    assert exinfo.value.message == ""
