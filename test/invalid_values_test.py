# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest
from pytest import raises, mark  # pylint: disable=no-name-in-module

from .utils.utils import config_error, config_warning, lineno, replace_ids, assert_lines_in

from .. import ConfigRoot, ConfigItem, ConfigException, MC_REQUIRED, MC_TODO
from ..envs import EnvFactory

ef = EnvFactory()

dev = ef.Env('dev')
tst = ef.Env('tst')
pp = ef.Env('pp')
prod = ef.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)


_attribute_mc_required_expected = """Attribute: 'a' MC_REQUIRED did not receive a value for current env Env('prod')"""

_attribute_mc_required_env_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "MC_REQUIRED"
}"""

def test_attribute_mc_required_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_env_expected_ex


_attribute_mc_required_default_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }
}"""

def test_attribute_mc_required_default(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', default=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_default_expected_ex


_attribute_mc_required_init_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen"
}"""

def test_attribute_mc_required_init(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp]):
            with ConfigItem(a=MC_REQUIRED) as ci:
                errorline = lineno() + 1
                ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_init_expected_ex


_attribute_mc_required_other_env_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "hi"
}"""

def test_attribute_mc_required_other_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod="hi", pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, """Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')""")
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_other_env_expected_ex


_attribute_mc_required_other_env_different_types_expected_ex = """There were 2 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "hi"
}"""

def test_attribute_mc_required_other_env_different_types(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [dev, prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', dev=1, prod="hi", pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()

    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s, dev <type 'int'>",
        "^%(lnum)s, prod <type 'str'>",
        "^ConfigError: Found different value types for property 'a' for different envs",
        "^%(lnum)s",
        "^ConfigError: Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')"
    )
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_other_env_different_types_expected_ex


def test_attribute_mc_required_default_all_overridden():
    with ConfigRoot(prod, [prod, pp]) as cr:
        cr.setattr('a', default=MC_REQUIRED, pp="hello", prod="hi")

    assert cr.a == "hi"


# MC_TODO

_attribute_mc_current_env_todo_expected = """Attribute: 'a' MC_TODO did not receive a value for current env Env('prod')"""
_attribute_mc_todo_other_env_expected = """Attribute: 'a' MC_TODO did not receive a value for env Env('prod')"""


# MC_TODO - Not Allowed for Current Env

_attribute_mc_todo_env_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "MC_TODO"
}"""

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp], mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_env_expected_ex


_attribute_mc_todo_default_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }
}"""

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_default(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp], mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('a', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_default_expected_ex


_attribute_mc_todo_init_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen"
}"""

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_init(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod, pp], mc_allow_todo=allow_todo):
            with ConfigItem(a=MC_TODO) as ci:
                errorline = lineno() + 1
                ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_init_expected_ex


_attribute_mc_required_mc_todo_different_types_expected_ex = """There were 3 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "MC_TODO"
}"""

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_required_mc_todo_different_types(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [dev, tst, pp, prod], mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('a', dev=1, tst="hello", pp=MC_REQUIRED, prod=MC_TODO)

    _sout, serr = capsys.readouterr()

    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s, dev <type 'int'>",
        "^%(lnum)s, tst <type 'str'>",
        "^ConfigError: Found different value types for property 'a' for different envs",
        "^%(lnum)s",
        "^ConfigError: Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')",
        "^%(lnum)s",
        "^ConfigError: Attribute: 'a' MC_TODO did not receive a value for env Env('prod')",
    )
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_mc_todo_different_types_expected_ex


# MC_TODO - Not Allowed for Other Envs

_attribute_mc_todo_other_env_env_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "pp"
    }, 
    "a": "hello"
}"""

def test_attribute_mc_todo_other_env_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(pp, [prod, pp], mc_allow_todo=False) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_todo_other_env_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_other_env_env_expected_ex


_attribute_mc_todo_other_env_default_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "pp"
    }, 
    "a": "hello"
}"""

def test_attribute_mc_todo_other_env_default(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(pp, [prod, pp], mc_allow_todo=False) as cr:
            errorline = lineno() + 1
            cr.setattr('a', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_todo_other_env_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_other_env_default_expected_ex


_attribute_mc_todo_other_env_init_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen", 
    "a": "hello"
}"""

def test_attribute_mc_todo_other_env_init(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(pp, [prod, pp]):
            with ConfigItem(a=MC_TODO) as ci:
                errorline = lineno() + 1
                ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_todo_other_env_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_other_env_init_expected_ex


# MC_TODO - Allowed Other Envs

@mark.parametrize("allow_current_env_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_env(capsys, allow_current_env_todo):
    with ConfigRoot(pp, [prod, pp], mc_allow_todo=True, mc_allow_current_env_todo=allow_current_env_todo) as cr:
        errorline = lineno() + 1
        cr.setattr('a', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_default_allowed_other_env(capsys):
    with ConfigRoot(pp, [prod, pp], mc_allow_todo=True, mc_allow_current_env_todo=False) as cr:
        errorline = lineno() + 1
        cr.setattr('a', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_init_allowed_other_env(capsys):
    with ConfigRoot(pp, [prod, pp], mc_allow_todo=True, mc_allow_current_env_todo=False):
        with ConfigItem(a=MC_TODO) as ci:
            errorline = lineno() + 1
            ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


# MC_TODO - Allowed Current Envs

_attribute_mc_current_env_todo_allowed_expected = _attribute_mc_current_env_todo_expected + ". Continuing with invalid configuration!"

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_envs(capsys, allow_todo):
    with ConfigRoot(prod, [prod, pp], mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        errorline = lineno() + 1
        cr.setattr('a', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_default_allowed_other_envs(capsys):
    with ConfigRoot(prod, [prod, pp], mc_allow_current_env_todo=True) as cr:
        errorline = lineno() + 1
        cr.setattr('a', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_init_allowed_other_envs(capsys):
    with ConfigRoot(prod, [prod, pp], mc_allow_current_env_todo=True):
        with ConfigItem(a=MC_TODO) as ci:
            errorline = lineno() + 1
            ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


_attribute_mc_required_mc_todo_different_types_allowed_expected_ex = """There were 2 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "a": "MC_TODO"
}"""
