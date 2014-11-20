# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest
from pytest import raises, mark  # pylint: disable=no-name-in-module

from .utils.utils import config_error, config_warning, lineno, replace_ids, assert_lines_in, replace_user_file_line_msg

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException, MC_REQUIRED, MC_TODO
from ..envs import EnvFactory

ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')

ef2_prod_pp_dev = EnvFactory()
dev2 = ef2_prod_pp_dev.Env('dev')
pp2 = ef2_prod_pp_dev.Env('pp')
prod2 = ef2_prod_pp_dev.Env('prod')

ef3_prod_pp_tst_dev = EnvFactory()
dev3 = ef3_prod_pp_tst_dev.Env('dev')
tst3 = ef3_prod_pp_tst_dev.Env('tst')
pp3 = ef3_prod_pp_tst_dev.Env('pp')
prod3 = ef3_prod_pp_tst_dev.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)


_attribute_mc_required_expected = """Attribute: 'a' MC_REQUIRED did not receive a value for current env Env('prod')"""

_attribute_mc_required_env_expected_ex = """There were %(num_errors)s errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": "MC_REQUIRED"
}"""

def test_attribute_mc_required_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_env_expected_ex % dict(num_errors=1)


_attribute_mc_required_override_env_expected = """
File "fake_dir/invalid_values_test.py", line %(line)s
ConfigError: Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')
File "fake_dir/invalid_values_test.py", line %(line)s
ConfigError: %(prod_err)s"""


def test_attribute_mc_required_override_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.override('a', MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    expected = _attribute_mc_required_override_env_expected.strip() % dict(line=errorline, prod_err=_attribute_mc_required_expected)
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline) == expected
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_env_expected_ex % dict(num_errors=2)


_attribute_mc_required_default_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": "MC_REQUIRED"
}"""

def test_attribute_mc_required_default(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('a', default=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    print _sout
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_default_expected_ex


_attribute_mc_required_init_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen",
    "a": "MC_REQUIRED"
}"""

def test_attribute_mc_required_init(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp):
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
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod="hi", pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    print _sout
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
        with ConfigRoot(prod2, ef2_prod_pp_dev) as cr:
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
    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        cr.setattr('a', default=MC_REQUIRED, pp="hello", prod="hi")

    assert cr.a == "hi"


def test_attribute_mc_required_init_args_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, a=MC_REQUIRED):
            super(Requires, self).__init__(a=a)

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires(a=3)

    assert cr.Requires.a == 3

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.a = 3

    assert cr.Requires.a == 3


_attribute_mc_required_other_env_requires_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "Requires #as: 'Requires', id: 0000, not-frozen",
    "a": "hi"
}"""


def test_attribute_mc_required_init_args_missing_env_value(capsys):
    class Requires(ConfigItem):
        def __init__(self, a=MC_REQUIRED):
            super(Requires, self).__init__(a=a)

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp):
            with Requires() as rq:
                errorline = lineno() + 1
                rq.setattr('a', prod='hi')

    _sout, serr = capsys.readouterr()
    print _sout
    assert serr == ce(errorline, """Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')""")
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_other_env_requires_expected_ex


_attribute_mc_required_init_args_missing_env_values_builder_expected_ex = """There were 2 errors when defining attribute 'a' on object: {
    "__class__": "Requires #as: 'Requires', id: 0000",
    "a": "MC_REQUIRED"
}"""

def test_attribute_mc_required_init_args_missing_env_values_builder(capsys):
    class Requires(ConfigItem):
        def __init__(self, a=MC_REQUIRED):
            super(Requires, self).__init__(a=a)

    class Builder(ConfigBuilder):
        def __init__(self):
            super(Builder, self).__init__()

        def build(self):
            Requires()

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp):
            with Builder():
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')",
        "^%(lnum)s",
        "^ConfigError: Attribute: 'a' MC_REQUIRED did not receive a value for current env Env('prod')",
    )
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_init_args_missing_env_values_builder_expected_ex


_attribute_mc_required_other_env_required_init_arg_missing_with_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "Requires #as: 'Requires', id: 0000",
    "a": "hi"
}"""

def test_attribute_mc_required_init_args_missing_with(capsys):
    class Requires(ConfigItem):
        def __init__(self, a=MC_REQUIRED):
            super(Requires, self).__init__()
            self.setattr('a', default=a, prod='hi')

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp):
            errorline = lineno() + 1
            Requires()

    _sout, serr = capsys.readouterr()
    print _sout
    assert serr == ce(errorline, """Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')""")
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_other_env_required_init_arg_missing_with_expected_ex


def test_attribute_mc_required_init_assign_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, a=MC_REQUIRED):
            super(Requires, self).__init__()
            self.a = a

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires(a=3)

    assert cr.Requires.a == 3

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.a = 3

    assert cr.Requires.a == 3


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
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('a', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    print _sout
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_env_expected_ex


_attribute_mc_todo_default_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "a": "MC_TODO"
}"""

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_default(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('a', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_default_expected_ex


_attribute_mc_todo_init_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "ConfigItem #as: 'ConfigItem', id: 0000, not-frozen",
    "a": "MC_TODO"
}"""

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_init(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo):
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
        with ConfigRoot(prod3, ef3_prod_pp_tst_dev, mc_allow_todo=allow_todo) as cr:
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
        "^ConfigError: Attribute: 'a' MC_TODO did not receive a value for current env Env('prod')",
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
        with ConfigRoot(pp1, ef1_prod_pp, mc_allow_todo=False) as cr:
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
        with ConfigRoot(pp1, ef1_prod_pp, mc_allow_todo=False) as cr:
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
        with ConfigRoot(pp1, ef1_prod_pp):
            with ConfigItem(a=MC_TODO) as ci:
                errorline = lineno() + 1
                ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_todo_other_env_expected)
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_todo_other_env_init_expected_ex


# MC_TODO - Allowed Other Envs

@mark.parametrize("allow_current_env_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_env(capsys, allow_current_env_todo):
    with ConfigRoot(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=allow_current_env_todo) as cr:
        errorline = lineno() + 1
        cr.setattr('a', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_default_allowed_other_env(capsys):
    with ConfigRoot(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=False) as cr:
        errorline = lineno() + 1
        cr.setattr('a', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_init_allowed_other_env(capsys):
    with ConfigRoot(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=False):
        with ConfigItem(a=MC_TODO) as ci:
            errorline = lineno() + 1
            ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


# MC_TODO - Allowed Current Envs

_continuing_with_invalid_conf = ". Continuing with invalid configuration!"
_attribute_mc_current_env_todo_allowed_expected = _attribute_mc_current_env_todo_expected + _continuing_with_invalid_conf

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_envs(capsys, allow_todo):
    with ConfigRoot(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        errorline = lineno() + 1
        cr.setattr('a', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_default_allowed_other_envs(capsys):
    with ConfigRoot(prod1, ef1_prod_pp, mc_allow_current_env_todo=True) as cr:
        errorline = lineno() + 1
        cr.setattr('a', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_init_allowed_other_envs(capsys):
    with ConfigRoot(prod1, ef1_prod_pp, mc_allow_current_env_todo=True):
        with ConfigItem(a=MC_TODO) as ci:
            errorline = lineno() + 1
            ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


_attribute_mc_current_env_todo_allowed_override_expected = """
File "fake_dir/invalid_values_test.py", line %(line)s
ConfigWarning: Attribute: 'a' MC_TODO did not receive a value for env Env('pp')
File "fake_dir/invalid_values_test.py", line %(line)s
ConfigWarning: %(prod_err)s
""".strip()

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_override_allowed_other_envs(capsys, allow_todo):
    with ConfigRoot(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        cr.a = 2
        errorline = lineno() + 1
        cr.override('a', MC_TODO)

    _sout, serr = capsys.readouterr()
    expected = _attribute_mc_current_env_todo_allowed_override_expected % dict(line=errorline, prod_err=_attribute_mc_current_env_todo_allowed_expected)
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline) == expected
