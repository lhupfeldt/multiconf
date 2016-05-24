# Copyright (c) 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from pytest import raises, mark  # pylint: disable=no-name-in-module

from .utils.utils import config_error, lineno, replace_ids, replace_user_file_line_msg

from .. import ConfigRoot, ConfigItem, ConfigException, MC_REQUIRED, MC_TODO
from ..envs import EnvFactory

ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


class ItemWithA(ConfigItem):
    def __init__(self, a=MC_REQUIRED):
        super(ItemWithA, self).__init__()
        self.a = a


_attribute_mc_required_expected = """Attribute: 'a' MC_REQUIRED did not receive a value for current env Env('prod')"""

_attribute_mc_required_env_expected_ex = """There %(ww)s %(num_errors)s %(err)s when defining attribute 'a' on object: {
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
            cr.setattr('a', prod="abc" + MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_required_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_expected_ex % dict(ww='was', num_errors=1, err='error')


_attribute_mc_required_override_env_expected = """
File "fake_dir/invalid_values_operations_test.py", line %(line)s
ConfigError: Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')
File "fake_dir/invalid_values_operations_test.py", line %(line)s
ConfigError: %(prod_err)s"""


def test_attribute_mc_required_override_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.override('a', MC_REQUIRED + "abc")

    _sout, serr = capsys.readouterr()
    expected = _attribute_mc_required_override_env_expected.strip() % dict(line=errorline, prod_err=_attribute_mc_required_expected)
    assert replace_user_file_line_msg(serr.strip(), line_no=errorline) == expected
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_expected_ex % dict(ww='were', num_errors=2, err='errors')


def test_attribute_mc_required_default_all_overridden():
    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        # TODO: This should actually not be allowed, it does not make sense!
        cr.setattr('a', default=1 + MC_REQUIRED, pp="hello", prod="hi")

    assert cr.a == "hi"


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, a=MC_REQUIRED):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('a', prod=a)
            self.setattr('b', default=17 + MC_REQUIRED, prod=2)

        def mc_init(self):
            self.a = 7
            self.b = 7

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires()

    assert cr.Requires.a == 7
    assert cr.Requires.b == 2

    with ConfigRoot(pp1, ef1_prod_pp) as cr:
        Requires()

    assert cr.Requires.a == 7
    assert cr.Requires.b == 7


# MC_TODO

_attribute_mc_current_env_todo_expected = """Attribute: 'a' MC_TODO did not receive a value for current env Env('prod')"""
_attribute_mc_todo_other_env_expected = """Attribute: 'a' MC_TODO did not receive a value for env Env('prod')"""


# MC_TODO - Not Allowed for Current Env

_attribute_mc_todo_env_expected_ex = """There was 1 error when defining attribute 'a' on object: {
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
            cr.setattr('a', prod="abc" + MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    print(_sout)
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_env_expected_ex


_attribute_mc_todo_default_expected_ex = """There was 1 error when defining attribute 'a' on object: {
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
            cr.setattr('a', default=MC_TODO.append("abc"), pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_default_expected_ex


_attribute_mc_todo_init_expected_ex = """There was 1 error when defining attribute 'a' on object: {
    "__class__": "ItemWithA #as: 'ItemWithA', id: 0000, not-frozen",
    "a": "MC_TODO"
}"""

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_init(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo):
            with ItemWithA(a=MC_TODO + MC_TODO) as ci:
                errorline = lineno() + 1
                ci.setattr('a', pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, _attribute_mc_current_env_todo_expected)
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_init_expected_ex
