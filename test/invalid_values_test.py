# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import pytest
from pytest import raises, mark  # pylint: disable=no-name-in-module

from .utils.utils import config_error, config_warning, lineno, replace_ids, assert_lines_in, replace_user_file_line_msg
from .utils.messages import already_printed_msg
from .utils.messages import config_error_mc_required_current_env_expected, config_error_mc_required_other_env_expected
from .utils.messages import mc_required_current_env_expected, mc_required_other_env_expected
from .utils.messages import mc_todo_current_env_expected, mc_todo_other_env_expected
from .utils.messages import config_error_mc_todo_current_env_expected
from .utils.tstclasses import RootWithAA, ItemWithAA

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


_attribute_mc_required_expected = mc_required_current_env_expected.format(attr='aa', env=prod1)

_attribute_mc_required_env_expected_ex = """There %(ww)s %(num_errors)s %(err)s when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg

def test_attribute_mc_required_env(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_expected_ex % dict(ww='was', num_errors=1, err='error')


def test_attribute_mc_required_override_env(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.override('aa', MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='aa', env=pp1),
        config_error_mc_required_current_env_expected.format(attr='aa', env=prod1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_expected_ex % dict(ww='were', num_errors=2, err='errors')


_attribute_mc_required_default_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg

def test_attribute_mc_required_default(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', default=MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    print(_sout)
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_default_expected_ex


_attribute_mc_required_init_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "aa": "MC_REQUIRED"
}""" + already_printed_msg

def test_attribute_mc_required_init(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp):
            with ItemWithAA(aa=MC_REQUIRED) as ci:
                errorline = lineno() + 1
                ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_init_expected_ex


_attribute_mc_required_other_env_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "hi"
}""" + already_printed_msg

def test_attribute_mc_required_other_env(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod="hi", pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    print(_sout)
    assert serr == ce(errorline, mc_required_other_env_expected.format(attr='aa', env=pp1))
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_other_env_expected_ex


_attribute_mc_required_other_env_different_types_expected_ex = """There were 2 errors when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "hi"
}""" + already_printed_msg

def test_attribute_mc_required_other_env_different_types(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod2, ef2_prod_pp_dev) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', dev=1, prod="hi", pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()

    assert_lines_in(
        __file__, errorline, serr,
        ("^%(lnum)s, dev <%(type_or_class)s 'int'>", "^%(lnum)s, prod <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='aa', env=pp1)
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_other_env_different_types_expected_ex


def test_attribute_mc_required_default_all_overridden():
    with RootWithAA(prod1, ef1_prod_pp) as cr:
        # TODO: This should actually not be allowed, it does not make sense!
        cr.setattr('aa', default=MC_REQUIRED, pp="hello", prod="hi")

    assert cr.aa == "hi"


def test_attribute_mc_required_init_args_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires(aa=3)

    assert cr.Requires.aa == 3

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.aa = 3

    assert cr.Requires.aa == 3


def test_attribute_mc_required_args_all_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

        def mc_init(self):
            if self.aa == MC_REQUIRED:
                self.aa = 7

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires()

    assert cr.Requires.aa == 7


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('b', default=MC_REQUIRED, prod=2)

        def mc_init(self):
            self.aa = 7
            self.b = 7

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires()

    assert cr.Requires.aa == 7
    assert cr.Requires.b == 2

    with ConfigRoot(pp1, ef1_prod_pp) as cr:
        Requires()

    assert cr.Requires.aa == 7
    assert cr.Requires.b == 7


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_with():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('b', default=MC_REQUIRED, prod=2)

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.aa = 7
            rq.setattr('b', pp=7)

    assert cr.Requires.aa == 7
    assert cr.Requires.b == 2

    with ConfigRoot(pp1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.aa = 7
            rq.setattr('b', pp=7)

    assert cr.Requires.aa == 7
    assert cr.Requires.b == 7


def test_attribute_mc_required_args_set_in_init_overridden_in_with():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.aa = 7

    assert cr.Requires.aa == 7

    with ConfigRoot(pp1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.aa = 7

    assert cr.Requires.aa == 7


_attribute_mc_required_other_env_requires_expected_ex = """There was 1 error when defining item: {
    "__class__": "Requires #as: 'Requires', id: 0000",
    "aa": "hi"
}""" + already_printed_msg


def test_attribute_mc_required_init_args_missing_env_value(capsys):
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp):
            with Requires() as rq:
                errorline = lineno() + 1
                rq.setattr('aa', prod='hi')

    _sout, serr = capsys.readouterr()
    print(_sout)
    assert serr == ce(errorline, mc_required_other_env_expected.format(attr='aa', env=pp1))
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_other_env_requires_expected_ex


_attribute_mc_required_init_args_missing_env_values_builder_expected_ex = """There were 2 errors when defining item: {
    "__class__": "Requires #as: 'Requires', id: 0000",
    "aa": "MC_REQUIRED"
}""" + already_printed_msg

def test_attribute_mc_required_init_args_missing_env_values_builder(capsys):
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

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
        config_error_mc_required_other_env_expected.format(attr='aa', env=pp1),
        config_error_mc_required_current_env_expected.format(attr='aa', env=prod1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_init_args_missing_env_values_builder_expected_ex


_attribute_mc_required_other_env_required_init_arg_missing_with_expected_ex = """There was 1 error when defining item: {
    "__class__": "Requires #as: 'Requires', id: 0000",
    "aa": "hi"
}""" + already_printed_msg

def test_attribute_mc_required_init_args_missing_with(capsys):
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.setattr('aa', default=aa, prod='hi')

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp):
            errorline = lineno() + 1
            Requires()

    _sout, serr = capsys.readouterr()
    print(_sout)
    assert serr == ce(errorline, mc_required_other_env_expected.format(attr='aa', env=pp1))
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_other_env_required_init_arg_missing_with_expected_ex


def test_attribute_mc_required_init_assign_all_overridden():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            self.aa = aa

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires(aa=3)

    assert cr.Requires.aa == 3

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        with Requires() as rq:
            rq.aa = 3

    assert cr.Requires.aa == 3


# MC_TODO

_attribute_mc_current_env_todo_expected = mc_todo_current_env_expected.format(attr='aa', env=prod1)
_attribute_mc_todo_other_env_expected = mc_todo_other_env_expected.format(attr='aa', env=prod1)


# MC_TODO - Not Allowed for Current Env

_attribute_mc_todo_env_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod_pp, mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_env_expected_ex


_attribute_mc_todo_default_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_default(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod1, ef1_prod_pp, mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_default_expected_ex


_attribute_mc_todo_init_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_init(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo):
            with ItemWithAA(aa=MC_TODO) as ci:
                errorline = lineno() + 1
                ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_init_expected_ex


_attribute_mc_required_mc_todo_different_types_expected_ex = """There were 3 errors when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_required_mc_todo_different_types(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with RootWithAA(prod3, ef3_prod_pp_tst_dev, mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', dev=1, tst="hello", pp=MC_REQUIRED, prod=MC_TODO)

    _sout, serr = capsys.readouterr()

    assert_lines_in(
        __file__, errorline, serr,
        ("^%(lnum)s, dev <%(type_or_class)s 'int'>", "^%(lnum)s, tst <%(type_or_class)s 'str'>"),
        "^ConfigError: Found different value types for property 'aa' for different envs",
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='aa', env=pp3),
        config_error_mc_todo_current_env_expected.format(attr='aa', env=prod3),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_mc_todo_different_types_expected_ex


# MC_TODO - Not Allowed for Other Envs

_attribute_mc_todo_other_env_env_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "hello"
}""" + already_printed_msg

def test_attribute_mc_todo_other_env_env(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(pp1, ef1_prod_pp, mc_allow_todo=False) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_todo_other_env_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_other_env_env_expected_ex


_attribute_mc_todo_other_env_default_expected_ex = """There was 1 error when defining item: {
    "__class__": "RootWithAA #as: 'RootWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "aa": "hello"
}""" + already_printed_msg

def test_attribute_mc_todo_other_env_default(capsys):
    with raises(ConfigException) as exinfo:
        with RootWithAA(pp1, ef1_prod_pp, mc_allow_todo=False) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_todo_other_env_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_other_env_default_expected_ex


_attribute_mc_todo_other_env_init_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "aa": "hello"
}""" + already_printed_msg

def test_attribute_mc_todo_other_env_init(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(pp1, ef1_prod_pp):
            with ItemWithAA(aa=MC_TODO) as ci:
                errorline = lineno() + 1
                ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_todo_other_env_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_other_env_init_expected_ex


# MC_TODO - Allowed Other Envs

@mark.parametrize("allow_current_env_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_env(capsys, allow_current_env_todo):
    with RootWithAA(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=allow_current_env_todo) as cr:
        errorline = lineno() + 1
        cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_default_allowed_other_env(capsys):
    with RootWithAA(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=False) as cr:
        errorline = lineno() + 1
        cr.setattr('aa', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


def test_attribute_mc_todo_init_allowed_other_env(capsys):
    with ConfigRoot(pp1, ef1_prod_pp, mc_allow_todo=True, mc_allow_current_env_todo=False):
        with ItemWithAA(aa=MC_TODO) as ci:
            errorline = lineno() + 1
            ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_todo_other_env_expected)


# MC_TODO - Allowed Current Envs

_continuing_with_invalid_conf = ". Continuing with invalid configuration!"
_attribute_mc_current_env_todo_allowed_expected = _attribute_mc_current_env_todo_expected + _continuing_with_invalid_conf

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env_allowed_other_envs(capsys, allow_todo):
    with RootWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        errorline = lineno() + 1
        cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_default_allowed_other_envs(capsys):
    with RootWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True) as cr:
        errorline = lineno() + 1
        cr.setattr('aa', default=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


def test_attribute_mc_todo_init_allowed_other_envs(capsys):
    with ConfigRoot(prod1, ef1_prod_pp, mc_allow_current_env_todo=True):
        with ItemWithAA(aa=MC_TODO) as ci:
            errorline = lineno() + 1
            ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)


@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env_allowed_current_env_access_error(capsys, allow_todo):
    """Test that accessing an MC_TODO value after loading results in an exception"""
    with RootWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        errorline = lineno() + 1
        cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, _attribute_mc_current_env_todo_allowed_expected)

    with raises(AttributeError) as exinfo:
        print(cr.aa)

    assert "Attribute 'aa' MC_TODO is undefined for current env " + repr(prod1) in str(exinfo.value)


@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_override_allowed_other_envs(capsys, allow_todo):
    with RootWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_allow_todo=allow_todo) as cr:
        cr.aa = 2
        errorline = lineno() + 1
        cr.override('aa', MC_TODO)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "ConfigWarning: " + mc_todo_other_env_expected.format(attr='aa', env=pp1),
        "ConfigWarning: " + mc_todo_current_env_expected.format(attr='aa', env=prod1),
    )


_attribute_mc_required_env_in_init_expected_ex = """There were %(num_errors)s errors when defining item: {
    "__class__": "MyRoot #as: 'MyRoot', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg


def test_attribute_mc_required_override_env_in_init(capsys):
    class MyRoot(ConfigRoot):
        def __init__(self, errorlines):
            super(MyRoot, self).__init__(prod1, ef1_prod_pp)
            errorlines.append( lineno() + 1)
            self.override('aa', MC_REQUIRED)

    errorlines = []
    with raises(ConfigException) as exinfo:
        MyRoot(errorlines)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorlines[0], serr,
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='aa', env=pp1),
        config_error_mc_required_current_env_expected.format(attr='aa', env=prod1),
    )

    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_in_init_expected_ex % dict(num_errors=2)


def test_multiple_attributes_mc_required_init_not_set(capsys):
    class ItemWithAAABBCC(ConfigItem):
        def __init__(self):
            super(ItemWithAAABBCC, self).__init__()
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED
            self.cc = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            ItemWithAAABBCC()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        config_error_mc_required_other_env_expected.format(attr='aa', env=pp1),
        config_error_mc_required_current_env_expected.format(attr='aa', env=prod1),
        config_error_mc_required_other_env_expected.format(attr='bb', env=pp1),
        config_error_mc_required_current_env_expected.format(attr='bb', env=prod1),
        config_error_mc_required_other_env_expected.format(attr='cc', env=pp1),
        config_error_mc_required_current_env_expected.format(attr='cc', env=prod1),
    )


_multiple_attributes_mc_required_env_expected_ex = """There %(ww)s %(num_errors)s %(err)s when defining item: {
    "__class__": "MyRoot #as: 'MyRoot', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_REQUIRED",
    "bb": 1
}""" + already_printed_msg

def test_multiple_attributes_mc_required_env(capsys):
    class MyRoot(ConfigRoot):
        def __init__(self, selected_env, env_factory):
            super(MyRoot, self).__init__(selected_env=selected_env, env_factory=env_factory)
            self.aa = MC_REQUIRED
            self.bb = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        with MyRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('aa', prod=MC_REQUIRED, pp="hello")
            cr.setattr('bb', prod=1, pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()
    assert ce(errorline, mc_required_current_env_expected.format(attr='aa', env=prod1)) in serr
    assert ce(errorline + 1, mc_required_other_env_expected.format(attr='bb', env=pp1)) in serr
    assert replace_ids(str(exinfo.value), False) == _multiple_attributes_mc_required_env_expected_ex % dict(ww='were', num_errors=2, err='errors')
