# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys

# pylint: disable=E0611
from pytest import raises

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigException
from ..decorators import nested_repeatables, named_as
from ..envs import EnvFactory

from .utils.utils import config_error, replace_ids, py3_local
from .utils.tstclasses import RootWithAA, ItemWithAA


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
        cr.setattr('bs?', prod=4)

    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(str(exinfo.value), named_as=False) == _t2_expected_repr


_find_contained_in_named_as_not_found_expected = """Searching from: <class 'multiconf.test.multiconf_access_errors_test.%(py3_local)sY'>: Could not find a parent container named as: 'notthere' in hieracy with names: ['someitems', 'x', 'someitems', 'x', 'root']"""

def test_find_contained_in_named_as_not_found():
    @named_as('someitems')
    @nested_repeatables('someitems')
    class NestedRepeatable(RepeatableConfigItem):
        def __init__(self, id):
            super(NestedRepeatable, self).__init__(mc_key=id)
            self.id = id
            self.a = None

    @named_as('x')
    @nested_repeatables('someitems')
    class X(ItemWithAA):
        pass

    @named_as('y')
    class Y(ItemWithAA):
        pass

    @nested_repeatables('someitems')
    class root(RootWithAA):
        pass

    with root(prod, ef1_prod) as cr:
        cr.aa = 0
        NestedRepeatable(id=0)
        with X() as ci:
            ci.setattr('aa', prod=0)
            NestedRepeatable(id='a')
            with NestedRepeatable(id='b') as ci:
                NestedRepeatable(id='c')
                with X() as ci:
                    ci.setattr('aa', prod=1)
                    with NestedRepeatable(id='d') as ci:
                        ci.setattr('a', prod=2)
                        with Y() as ci:
                            ci.setattr('aa', prod=3)

    with raises(ConfigException) as exinfo:
        cr.x.someitems['b'].x.someitems['d'].y.find_contained_in(named_as='notthere').a

    assert replace_ids(str(exinfo.value)) == _find_contained_in_named_as_not_found_expected % dict(py3_local=py3_local())


_find_attribute_with_attribute_name_not_found = """Searching from: <class 'multiconf.test.multiconf_access_errors_test.%(py3_local)sX'>: Could not find an attribute named: 'e' in hieracy with names: ['x', 'someitems', 'x', 'someitems', 'x', 'root']"""

def test_find_attribute_with_attribute_name_not_found():
    @named_as('someitems')
    @nested_repeatables('someitems')
    class NestedRepeatable(RepeatableConfigItem):
        def __init__(self, id):
            super(NestedRepeatable, self).__init__(mc_key=id)
            self.id = id
            self.a = None

    @named_as('x')
    @nested_repeatables('someitems')
    class X(ItemWithAA):
        pass

    @nested_repeatables('someitems')
    class root(ConfigRoot):
        def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                     mc_allow_todo=False, mc_allow_current_env_todo=False):
            super(root, self).__init__(
                selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
                mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)
            self.a = None
            self.q = None

    with root(prod, ef1_prod) as cr:
        cr.a = 0
        cr.q = 17
        NestedRepeatable(id=1)
        with X() as ci:
            ci.setattr('aa', prod=0)
            with NestedRepeatable(id='a') as nr:
                nr.a = 9
            with NestedRepeatable(id='b') as ci:
                with NestedRepeatable(id='c') as nr:
                    nr.a = 7
                with X() as ci:
                    ci.aa = 1
                    ci.setattr('b?', prod=1)
                    with NestedRepeatable(id='d') as ci:
                        ci.setattr('a', prod=2)
                        with X() as ci:
                            ci.setattr('aa', prod=3)

    with raises(ConfigException) as exinfo:
        assert cr.x.someitems['b'].x.someitems['d'].x.find_attribute('e') == 3

    assert replace_ids(str(exinfo.value)) == _find_attribute_with_attribute_name_not_found % dict(py3_local=py3_local())


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
