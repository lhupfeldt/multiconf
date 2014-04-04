#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from .utils.utils import api_error, lineno

from .. import ConfigRoot, ConfigItem, ConfigApiException, ConfigException
from ..decorators import nested_repeatables, repeat
from ..envs import EnvFactory

ef = EnvFactory()

dev2ct = ef.Env('dev2CT')
dev2st = ef.Env('dev2ST')
g_dev2 = ef.EnvGroup('g_dev2', dev2ct, dev2st)

dev3ct = ef.Env('dev3CT')
dev3st = ef.Env('dev3ST')
g_dev3 = ef.EnvGroup('g_dev3', dev3ct, dev3st)

g_dev = ef.EnvGroup('g_dev', g_dev2, g_dev3)

pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod = ef.EnvGroup('g_prod', pp, prod)

valid_envs = ef.EnvGroup('g_all', g_dev, g_prod)


_expected_ex_msg = "An error was detected trying to get attribute '%s' on class 'inner'"
_extra_stderr = """
    - Attributes starting with '_mc' are reserved for internal MultiConf usage. You probably tried to use the
      MultiConf API in a derived class __init__ before calling the parent class __init__"""


def capie(line_num, *lines):
    return api_error(__file__, line_num, *lines)


@nested_repeatables('RepeatableItems')
class project(ConfigRoot):
    pass


@repeat()
class RepeatableItem(ConfigItem):
    pass


def test_find_contained_in_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass
        
        class inner(ConfigItem):
            def __init__(self, **kwargs):
                global inner_errorline
                # Error: find_contained_in must not be called before parent __init__
                inner_errorline = lineno() + 1
                self.find_contained_in('a')

        with root(prod, [prod, pp], a=0):
            inner(id='n1', b=1)
    
    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % '_mc_contained_in'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert exinfo.value.message == eex


def test_property_method_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass
        
        class inner(ConfigItem):
            def __init__(self, **kwargs):
                global inner_errorline
                # Error: env must not be called before parent __init__
                inner_errorline = lineno() + 1
                print(self.env)

        with root(prod, [prod, pp], a=0):
            inner(id='n1', b=1)
    
    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % '_mc_root_conf'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert exinfo.value.message == eex


def test_undefined_method_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass
        
        class inner(ConfigItem):
            def __init__(self, **kwargs):
                global inner_errorline
                inner_errorline = lineno() + 1
                self.ttt('')

        with root(prod, [prod, pp], a=0):
            inner(id='n1', b=1)
        
    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % '_mc_attributes'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert exinfo.value.message == eex


def test_undefined_property_method_called_before_parent___init__(capsys):
    with raises(ConfigApiException) as exinfo:
        class root(ConfigRoot):
            pass
        
        class inner(ConfigItem):
            def __init__(self, **kwargs):
                global inner_errorline
                inner_errorline = lineno() + 1
                self.ttt

        with root(prod, [prod, pp], a=0):
            inner(id='n1', b=1)
        
    _sout, serr = capsys.readouterr()
    eex = _expected_ex_msg % '_mc_attributes'
    assert serr == capie(inner_errorline, eex + _extra_stderr)
    assert exinfo.value.message == eex


def test_setattr_multiconf_private_attribute():
    class root(ConfigRoot):
        pass
        
    class inner(ConfigItem):
        pass

    ex_msg = """Trying to set attribute '_mc_whatever' on a config item. Atributes starting with '_mc' are reserved for multiconf internal usage."""

    with raises(ConfigException) as exinfo:
        with root(prod, [prod, pp], a=0) as cr:
            cr.setattr('_mc_whatever', default=1)

    assert exinfo.value.message == ex_msg        

    with raises(ConfigException) as exinfo:
        with root(prod, [prod, pp], a=0) as cr:
            with inner(id='n1', b=1) as ci:
                ci.setattr('_mc_whatever', default=1)

    assert exinfo.value.message == ex_msg


def test_setattr_to_attribute_underscore_attribute():
    ex_msg = """Trying to set attribute '_b' on a config item. Atributes starting with '_' can not be set using item.setattr. Use assignment instead."""
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod]):
            with ConfigItem() as ci:
                ci.setattr('_b', default=7)

    assert exinfo.value.message == ex_msg


def test_getattr_repr_error():
    class X(ConfigItem):
        def __repr__(self):
            raise Exception("Bad repr")

    with raises(AttributeError) as exinfo:
        with ConfigRoot(prod, [prod, pp]):
            x = X()
            _ = x.a

    assert "X'> has no attribute 'a'" in exinfo.value.message
