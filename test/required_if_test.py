# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises
from .utils.utils import config_error, config_warning, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import required_if
from ..envs import EnvFactory

ef = EnvFactory()

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

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)


def test_required_if_attributes_condition_true_prod_and_condition_unset_dev2ct():
    @required_if('a', 'b, c')
    class root(ConfigRoot):
        pass

    with root(prod, [prod, dev2ct]) as cr:
        cr.setattr('a', prod=10)
        cr.setattr('b', prod=20)
        cr.setattr('c', prod=30)
        cr.setattr('d', prod=40, dev2ct=41)

    assert cr.a == 10
    assert cr.b == 20
    assert cr.c == 30
    assert cr.d == 40

    # Test iteritems
    expected_keys = ['a', 'b', 'c', 'd']
    index = 0
    for key, val in cr.iteritems():
        assert key == expected_keys[index]
        assert val == (index + 1) * 10
        index += 1
    assert index == 4


def conf1(env):
    @required_if('a', 'b, c')
    class root(ConfigRoot):
        pass

    with root(env, [prod, dev2ct]) as cr:
        cr.setattr('a', prod=0, dev2ct=1)
        cr.setattr('b', prod=10, dev2ct=11)
        cr.setattr('c', dev2ct=21)

    return cr


def test_required_if_attributes_condition_false_instantiated_env():
    cr = conf1(prod)
    assert cr.a == 0
    assert cr.b == 10
    assert not hasattr(cr, 'c')

    # Test iteritems
    expected_keys = ['a', 'b']
    index = 0
    for key, val in cr.iteritems():
        assert key == expected_keys[index]
        assert val == index * 10
        index += 1
    assert index == 2


def test_required_if_attributes_condition_true_other_env():
    cr = conf1(dev2ct)
    assert cr.a == 1
    assert cr.b == 11
    assert cr.c == 21

    # Test iteritems
    expected_keys = ['a', 'b', 'c']
    index = 0
    for key, val in cr.iteritems():
        assert key == expected_keys[index]
        assert val == index * 10 + 1
        index += 1
    assert index == 3


def test_required_if_condition_attribute_missing():
    class root(ConfigRoot):
        pass

    @required_if('abcd', 'efgh, ijkl')
    class item(ConfigItem):
        pass

    with root(prod, [prod]):
        with item() as it:
            it.setattr('a', prod=2)

    # The above code is valid, the condition attribute i not mandatory
    assert 1 == 1


def test_required_if_condition_attribute_missing_other_attribute_default_value():
    class root(ConfigRoot):
        pass

    @required_if('abcd', 'efgh, ijkl')
    class item(ConfigItem):
        pass

    with root(prod, [prod]):
        item(a=1)
    # The above code is valid, the condition attribute i not mandatory
    assert 1 == 1


def test_required_if_condition_attribute_missing_no_other_attributes():
    class root(ConfigRoot):
        pass

    @required_if('abcd', 'efgh, ijkl')
    class item(ConfigItem):
        pass

    with root(prod, [prod]):
        item()
    # The above code is valid, the condition attribute i not mandatory
    assert 1 == 1


_missing_fully_expected = """Missing required_if attributes. Condition attribute: 'abcd' == 1, missing attributes: ['efgh', 'ijkl']"""

def test_required_if_optional_attributes_missing_fully_instantiated_env():
    with raises(ConfigException) as exinfo:
        class root(ConfigRoot):
            pass

        @required_if('abcd', 'efgh, ijkl, ihasit')
        class item(ConfigItem):
            pass

        with root(prod, [prod, dev2ct]):
            with item() as ii:
                ii.setattr('abcd', prod=1, dev2ct=0)
                ii.setattr('ihasit', prod=7, dev2ct=8)

    assert exinfo.value.message == _missing_fully_expected


# NOTE: This cannot be reliably determined and may cause false errors in case of derived attributes
# required_if can only be validated for instantiated env
#def test_required_if_optional_attributes_missing_fully_other_env():
#    with raises(ConfigException) as exinfo:
#        class root(ConfigRoot):
#            pass
#
#        @required_if('abcd', 'efgh, ijkl')
#        class item(ConfigItem):
#            pass
#
#        with root(dev2ct, [prod, dev2ct]):
#            with item() as ii:
#                ii.setattr('abcd', prod=1, dev2ct=0)
#                ii.setattr('ihasit', prod=7, dev2ct=8)
#
#    assert exinfo.value.message == _missing_fully_expected


def test_required_if_optional_attributes_missing_some_env_instantiated_env():
    with raises(ConfigException) as exinfo:
        class root(ConfigRoot):
            pass

        @required_if('abcd', 'efgh, ijkl, ihasit')
        class item(ConfigItem):
            pass

        with root(prod, [prod, dev2ct, dev3ct]):
            with item() as ii:
                ii.setattr('abcd', prod=1, dev2ct=0, dev3ct=17)
                ii.setattr('efgh', prod=2)
                ii.setattr('ijkl', dev2ct=3)
                ii.setattr('ihasit', prod=7, dev2ct=8)

    # TODO improve error message
    assert True


def test_required_if_optional_attributes_missing_some_env_other_env():
    with raises(ConfigException) as exinfo:
        class root(ConfigRoot):
            pass

        @required_if('abcd', 'efgh, ijkl')
        class item(ConfigItem):
            pass

        with root(dev2ct, [prod, dev2ct, dev3ct]):
            with item() as ii:
                ii.setattr('abcd', prod=1, dev2ct=0, dev3ct=17)
                ii.setattr('efgh', prod=2)
                ii.setattr('ijkl', dev2ct=3)
                ii.setattr('ihasit', prod=7, dev2ct=8)

    # TODO improve error message
    assert True


_expected_regular_attributes_missing_when_required_if_used_ex = """There were 1 errors when defining attribute 'x' on object: {
    "__class__": "item #as: 'xxxx', id: 0000, not-frozen", 
    "abcd": 0
}"""

def test_regular_attributes_missing_when_required_if_used():
    with raises(ConfigException) as exinfo:
        class root(ConfigRoot):
            pass

        @required_if('abcd', 'efgh, ijkl')
        class item(ConfigItem):
            pass

        with root(prod, [prod, dev2ct]):
            with item() as ii:
                ii.setattr('abcd', prod=0)
                ii.setattr('x', dev2ct=0)
                ii.setattr('y', prod=0)

    assert replace_ids(exinfo.value.message) == _expected_regular_attributes_missing_when_required_if_used_ex
