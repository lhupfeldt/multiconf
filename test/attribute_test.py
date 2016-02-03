# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from ..attribute import Attribute, Where, SetAttrSemantic
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

ef._mc_create_default_group()
default_group = ef.env_or_group_from_name('default')


def test_unset_attribute_repr():
    attr = Attribute(setattr_semantic=SetAttrSemantic.STD)
    assert repr(attr) == "Attribute: not-frozen, value: MC_NO_VALUE 0b0000000000000000, None:None Where.NOWHERE"
    attr._mc_frozen = True  # pylint: disable=protected-access
    assert repr(attr) == "Attribute: frozen, value: MC_NO_VALUE 0b0000000000000000, None:None Where.NOWHERE"


def test_attribute_default():
    attr1 = Attribute(setattr_semantic=SetAttrSemantic.STD)
    assert not attr1.all_set(0b1111)
    assert attr1._value == _MC_NO_VALUE  # pylint: disable=protected-access
    assert attr1._mc_value() == _MC_NO_VALUE  # pylint: disable=protected-access

    assert not attr1.all_set(0b1111)
    assert not attr1.all_set(default_group.bit)
    assert not attr1.all_set(default_group.mask)
    assert attr1._mc_frozen is False  # pylint: disable=protected-access

    attr1.set_env_provided(default_group)
    attr1.set_current_env_value(None, default_group, Where.IN_WITH, __file__, 999)
    assert attr1.all_set(default_group.mask)
    assert attr1._mc_value() is None  # pylint: disable=protected-access
    assert attr1._mc_frozen is True  # pylint: disable=protected-access

    attr2 = Attribute(setattr_semantic=SetAttrSemantic.STD)
    assert not attr2.all_set(default_group.mask)

    attr2.set_env_provided(default_group)
    attr2.set_current_env_value(13, default_group, Where.IN_WITH, __file__, 999)
    assert attr2.all_set(default_group.mask)
    assert attr2._mc_value() == 13  # pylint: disable=protected-access


def test_attribute_env_set():
    attr1 = Attribute(setattr_semantic=SetAttrSemantic.STD)

    attr1.set_env_provided(dev1a)
    attr1.set_current_env_value(None, dev1a, Where.IN_WITH, __file__, 999)
    assert attr1._mc_value() == None  # pylint: disable=protected-access
    assert attr1.all_set(dev1a.mask)
    assert not attr1.all_set(dev1a.mask | prod.mask)
    assert not attr1.all_set(dev1a.mask | g_prod.mask)
    assert not attr1.all_set(g_dev1.mask)
    assert not attr1.all_set(dev1b.mask)
    attr1.set_current_env_value(3, dev1a, Where.IN_WITH, __file__, 123)
    assert attr1._mc_value() == 3  # pylint: disable=protected-access

    assert repr(attr1) == "Attribute: frozen, value: 3 0b0000000000000010, %s:123 Where.IN_WITH" % repr(__file__)


def test_attribute_where_from_repr():
    attr1 = Attribute(setattr_semantic=SetAttrSemantic.STD)

    attr1.set_env_provided(dev1a)
    attr1.set_current_env_value(None, dev1a, Where.IN_WITH, __file__, 999)
    assert attr1._mc_value() == None  # pylint: disable=protected-access
    assert repr(attr1) == "Attribute: frozen, value: None 0b0000000000000010, %s:999 Where.IN_WITH" % repr(__file__)

    attr2 = Attribute(setattr_semantic=SetAttrSemantic.STD)
    attr2.set_env_provided(dev1b)
    attr2.set_current_env_value(2, dev1a, Where.IN_INIT, __file__, 123)
    assert repr(attr2) == "Attribute: not-frozen, value: 2 0b0000000000000100, %s:123 Where.IN_INIT" % repr(__file__)

    attr3 = Attribute(setattr_semantic=SetAttrSemantic.STD)
    attr3.set_env_provided(dev1b)
    attr3.set_current_env_value(3, dev1a, Where.IN_INIT, __file__, 123)
    assert repr(attr3) == "Attribute: not-frozen, value: 3 0b0000000000000100, %s:123 Where.IN_INIT" % repr(__file__)


def test_attribute_env_provided():
    attr1 = Attribute(setattr_semantic=SetAttrSemantic.STD)

    attr1.set_env_provided(dev1a)
    assert attr1._mc_value() == _MC_NO_VALUE  # pylint: disable=protected-access
    assert attr1.all_set(dev1a.mask)
    assert repr(attr1) == "Attribute: not-frozen, value: MC_NO_VALUE 0b0000000000000010, None:None Where.NOWHERE"
    assert not attr1.all_set(dev1a.mask | prod.mask)
    assert not attr1.all_set(dev1a.mask | g_prod.mask)
    assert not attr1.all_set(g_dev1.mask)
    assert not attr1.all_set(dev1b.mask)

    attr1.set_env_provided(prod)
    assert attr1.all_set(dev1a.mask)
    assert attr1.all_set(prod.mask)
    assert attr1.all_set(dev1a.mask | prod.mask)

    attr1.set_current_env_value(3, dev1a, Where.IN_WITH, __file__, 123)
    assert attr1._mc_value() == 3  # pylint: disable=protected-access

    assert repr(attr1) == "Attribute: frozen, value: 3 0b0000001000000010, %s:123 Where.IN_WITH" % repr(__file__)
