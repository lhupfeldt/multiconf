# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import sys

# pylint: disable=E0611
from pytest import raises, xfail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException
from multiconf.config_errors import ConfigAttributeError
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import config_error, replace_ids, py3_local
from .utils.tstclasses import ItemWithAA


ef1_prod = EnvFactory()

prod = ef1_prod.Env('prod')

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_access_undefined_attribute_expected_repr = """{
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    }
}, object of type: <class 'multiconf.multiconf.ConfigItem'> has no attribute 'b'"""

def test_access_undefined_attribute():
    @mc_config(ef1_prod)
    def _(_):
        ConfigItem()

    cr = ef1_prod.config(prod).ConfigItem

    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(str(exinfo.value), named_as=False) == _access_undefined_attribute_expected_repr


_t2_expected_repr = """{
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "bs": 4
}, object of type: <class 'multiconf.multiconf.ConfigItem'> has no attribute 'b', but found attribute 'bs'"""

def test_access_undefined_attribute_but_has_repeatable_attribute_with_attribute_name_plus_s():
    @mc_config(ef1_prod)
    def _(_):
        with ConfigItem() as cr:
            cr.setattr('bs', prod=4, mc_set_unknown=True)

    cr = ef1_prod.config(prod).ConfigItem

    # ConfigAttributeError is instance of AttributeError
    with raises(ConfigAttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(str(exinfo.value), named_as=False) == _t2_expected_repr


# TODO
#def test_error_in_property_method_implementation(self):
#    class root(ConfigItem):
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