#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises
from .utils.utils import config_error, config_warning, lineno

from .. import ConfigRoot, ConfigItem, ConfigException
from ..decorators import required, required_if, optional, nested_repeatables, ConfigDefinitionException
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


def test_required_attributes_missing_for_configroot():
    with raises(ConfigException) as exinfo:
        @required('someattr1, someattr2')
        class root(ConfigRoot):
            pass

        with root(prod, [prod]):
            pass

    assert exinfo.value.message == "No value given for required attributes: ['someattr1', 'someattr2']"


def test_required_attributes_missing_for_configitem():
    with raises(ConfigException) as exinfo:
        class root(ConfigRoot):
            pass

        @required('abcd, efgh, ijkl')
        class item(ConfigItem):
            pass

        with root(prod, [prod]):
            with item() as ii:
                ii.setattr('efgh', prod=7)

    assert exinfo.value.message == "No value given for required attributes: ['abcd', 'ijkl']"


def test_optional_attribute_accessed_for_env_where_not_specified():
    @optional('a')
    class root(ConfigRoot):
        pass

    with raises(AttributeError) as exinfo:
        with root(prod, [prod, dev2ct]) as cr:
            cr.setattr('a', dev2ct=18)

        print(cr.a)

    assert exinfo.value.message == "Attribute 'a' undefined for env Env('prod')"

def test_decorator_arg_not_a_valid_identifier_in_required_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @required('a, a-b, b, 99')
        class root(ConfigRoot):
            pass

    assert exinfo.value.message == "['a-b', '99'] are not valid identifiers"


def test_decorator_arg_is_keyword_in_nested_repeatables_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @nested_repeatables('a, b, def, c')
        class root(ConfigRoot):
            pass

    assert exinfo.value.message == "'def' is not a valid identifier"

def test_decorator_args_are_keywords_in_required_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @required('a, class, b, 99')
        class root(ConfigRoot):
            pass

    assert exinfo.value.message == "['class', '99'] are not valid identifiers"


def test_decorator_arg_not_a_valid_identifier_in_required_if_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @required_if('-a', 'a, a-b, b, 99')
        class root(ConfigRoot):
            pass

    assert exinfo.value.message == "['-a', 'a-b', '99'] are not valid identifiers"


def test_required_attributes_inherited_missing():
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    @required('someattr2, someotherattr2')
    class root2(root):
        pass

    with raises(ConfigException) as exinfo:
        with root2(prod, [prod]) as cr:
            cr.setattr('anattr', prod=1)
            cr.setattr('someattr2', prod=3)
            cr.setattr('someotherattr2', prod=4)

    assert exinfo.value.message == "No value given for required attributes: ['anotherattr']"


def test_required_attributes_inherited_redefined(capsys):
    @required('anattr, anotherattr')
    class root(ConfigRoot):
        pass

    errorline = lineno() + 2
    @required('anattr, someotherattr2')
    class root2(root):
        pass

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, "Attribute name: 'anattr' re-specified as 'required' on class: 'root2' , was already inherited from a super class.")
