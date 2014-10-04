# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from ..attribute import Attribute, mc_where_from_init, mc_where_from_with, mc_where_from_mc_init, where_from_name
from ..values import MC_REQUIRED, _MC_NO_VALUE
from ..envs import EnvFactory


ef = EnvFactory()

dev1a = ef.Env('dev1a')
dev1b = ef.Env('dev1b')
g_dev1 = ef.EnvGroup('g_dev1', dev1a, dev1b)

dev2a = ef.Env('dev2a')
dev2b = ef.Env('dev2b')
g_dev2 = ef.EnvGroup('g_dev2', dev2a, dev2b)

g_dev = ef.EnvGroup('g_dev', g_dev1, g_dev2)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

ef._mc_init_and_default_groups()
default_group = ef.env_or_group_from_name('default')
init_group = ef.env_or_group_from_name('__init__')


def test_unset_attribute_repr():
    attr = Attribute(name='some_name1')
    assert repr(attr) == "Attribute: 'some_name1':not-frozen, value: _MC_NO_VALUE 0b0000000000000000, None:None from_nowhere"
    attr._mc_frozen = True  # pylint: disable=protected-access
    assert repr(attr) == "Attribute: 'some_name1':frozen, value: _MC_NO_VALUE 0b0000000000000000, None:None from_nowhere"


def test_attribute_default():
    attr1 = Attribute(name='some_name2a')
    assert not attr1.all_set(0b1111)
    assert attr1._value == _MC_NO_VALUE  # pylint: disable=protected-access
    assert attr1._mc_value() == _MC_NO_VALUE  # pylint: disable=protected-access

    assert not attr1.all_set(0b1111)
    assert not attr1.all_set(default_group.bit)
    assert not attr1.all_set(default_group.mask)
    assert attr1._mc_frozen == False  # pylint: disable=protected-access

    attr1.set_env_provided(default_group)
    attr1.set_current_env_value(None, default_group, mc_where_from_with, __file__, 999)
    assert attr1.all_set(default_group.mask)
    assert attr1._mc_value() == None  # pylint: disable=protected-access
    assert attr1._mc_frozen == True  # pylint: disable=protected-access

    attr2 = Attribute(name='some_name2b')
    assert not attr2.all_set(init_group.bit)
    assert not attr2.all_set(default_group.mask)

    attr2.set_env_provided(default_group)
    attr2.set_current_env_value(13, default_group, mc_where_from_with, __file__, 999)
    assert attr2.all_set(default_group.mask)
    assert attr2._mc_value() == 13  # pylint: disable=protected-access


def test_attribute_env_set():
    attr1 = Attribute(name='some_name3a')

    attr1.set_env_provided(dev1a)
    attr1.set_current_env_value(None, dev1a, mc_where_from_with, __file__, 999)
    assert attr1._mc_value() == None  # pylint: disable=protected-access
    assert attr1.all_set(dev1a.mask)
    assert not attr1.all_set(dev1a.mask | prod.mask)
    assert not attr1.all_set(dev1a.mask | g_prod.mask)
    assert not attr1.all_set(g_dev1.mask)
    assert not attr1.all_set(dev1b.mask)
    attr1.set_current_env_value(3, dev1a, mc_where_from_with, __file__, 123)
    assert attr1._mc_value() == 3  # pylint: disable=protected-access

    assert repr(attr1) == "Attribute: 'some_name3a':frozen, value: 3 0b0000000000000010, %s:123 from_with" % repr(__file__)


def test_attribute_where_from_repr():
    attr1 = Attribute(name='some_name3a')

    attr1.set_env_provided(dev1a)
    attr1.set_current_env_value(None, dev1a, mc_where_from_with, __file__, 999)
    assert attr1._mc_value() == None  # pylint: disable=protected-access
    assert repr(attr1) == "Attribute: 'some_name3a':frozen, value: None 0b0000000000000010, %s:999 from_with" % repr(__file__)

    attr2 = Attribute(name='some_name3b')
    attr2.set_env_provided(dev1b)
    attr2.set_current_env_value(2, dev1a, mc_where_from_init, __file__, 123)
    assert repr(attr2) == "Attribute: 'some_name3b':not-frozen, value: 2 0b0000000000000100, %s:123 from_init" % repr(__file__)

    attr3 = Attribute(name='some_name3c')
    attr3.set_env_provided(dev1b)
    attr3.set_current_env_value(3, dev1a, mc_where_from_init, __file__, 123)
    assert repr(attr3) == "Attribute: 'some_name3c':not-frozen, value: 3 0b0000000000000100, %s:123 from_init" % repr(__file__)

    assert where_from_name(mc_where_from_init) == "from_init"
    assert where_from_name(mc_where_from_mc_init) == "from_mc_init"

    with raises(Exception) as exinfo:
        where_from_name(12312334234)
    assert exinfo.value.message == "Not a where_from value:12312334234"


def test_attribute_env_provided():
    attr1 = Attribute(name='some_name4a')

    attr1.set_env_provided(dev1a)
    assert attr1._mc_value() == _MC_NO_VALUE  # pylint: disable=protected-access
    assert attr1.all_set(dev1a.mask)
    assert repr(attr1) == "Attribute: 'some_name4a':not-frozen, value: _MC_NO_VALUE 0b0000000000000010, None:None from_nowhere"
    assert not attr1.all_set(dev1a.mask | prod.mask)
    assert not attr1.all_set(dev1a.mask | g_prod.mask)
    assert not attr1.all_set(g_dev1.mask)
    assert not attr1.all_set(dev1b.mask)

    attr1.set_env_provided(prod)
    assert attr1.all_set(dev1a.mask)
    assert attr1.all_set(prod.mask)
    assert attr1.all_set(dev1a.mask | prod.mask)

    attr1.set_current_env_value(3, dev1a, mc_where_from_with, __file__, 123)
    assert attr1._mc_value() == 3  # pylint: disable=protected-access

    assert repr(attr1) == "Attribute: 'some_name4a':frozen, value: 3 0b0000001000000010, %s:123 from_with" % repr(__file__)
