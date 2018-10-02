# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem
from multiconf.envs import EnvFactory

from .utils.utils import config_error, replace_ids
from .utils.tstclasses import ItemWithAA


ef = EnvFactory()

pprd = ef.Env('pprd')
prod = ef.Env('prod')

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_access_undefined_attribute_expected_repr = "'ConfigItem' object has no attribute 'b'"

def test_access_undefined_attribute():
    @mc_config(ef, load_now=True)
    def config(_):
        ConfigItem()

    cr = config(prod).ConfigItem
    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(str(exinfo.value), named_as=False) == _access_undefined_attribute_expected_repr


# We can't tell about the 'bs' attribute here because it is completely handled by Python now
_t2_expected_repr = "'ConfigItem' object has no attribute 'b'"

def test_access_undefined_attribute_but_has_repeatable_attribute_with_attribute_name_plus_s():
    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem() as cr:
            cr.setattr('bs', pprd=1, prod=4, mc_set_unknown=True)

    cr = config(prod).ConfigItem

    with raises(AttributeError) as exinfo:
        print(cr.b)

    assert replace_ids(str(exinfo.value), named_as=False) == _t2_expected_repr


def test_access_undefined_attribute_json_single_level():
    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithAA(17):
            with ConfigItem():
                ConfigItem()

    cr = config(prod).ItemWithAA

    with raises(AttributeError) as exinfo:
        print(cr.b)

    print(exinfo.value)

    assert str(exinfo.value) == "'ItemWithAA' object has no attribute 'b'"


_access_undefined_private_attribute_expected_repr = "'ConfigItem' object has no attribute '_b'"

def test_access_undefined_private_attribute():
    @mc_config(ef, load_now=True)
    def config(_):
        ConfigItem()

    cr = config(prod).ConfigItem
    with raises(AttributeError) as exinfo:
        print(cr._b)

    assert replace_ids(str(exinfo.value), named_as=False) == _access_undefined_private_attribute_expected_repr


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
#    with root(prod, ef) as cr:
#        X()
#
#    with raises(ConfigException) as exinfo:
#        a = cr.x.method
#
#    assert str(exinfo.value) == ""
