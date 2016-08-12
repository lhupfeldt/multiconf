# Copyright (c) 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from pytest import raises, mark  # pylint: disable=no-name-in-module

from .utils.utils import config_error, lineno, replace_ids, replace_user_file_line_msg, total_msg, assert_lines_in, file_line
from .utils.messages import already_printed_msg
from .utils.messages import config_error_mc_required_current_env_expected, config_error_mc_required_other_env_expected
from .utils.messages import mc_todo_current_env_expected, mc_todo_other_env_expected
from .utils.tstclasses import ItemWithAA


from .. import ConfigRoot, ConfigItem, ConfigException, MC_REQUIRED, MC_TODO
from ..envs import EnvFactory

ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_attribute_mc_required_env_expected_ex = """There %(ww)s %(num_errors)s %(err)s when defining item: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_REQUIRED"
}""" + already_printed_msg


def test_attribute_mc_required_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.setattr('aa?', prod="abc" + MC_REQUIRED, pp="hello")

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, None, serr,
        file_line(errorline),
        config_error_mc_required_current_env_expected.format(attr='aa', env=prod1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_expected_ex % dict(ww='was', num_errors=1, err='error')
    assert total_msg(1) in str(exinfo.value)


def test_attribute_mc_required_override_env(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            errorline = lineno() + 1
            cr.override('aa?', MC_REQUIRED + "abc")

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, None, serr,
        file_line(errorline),
        config_error_mc_required_other_env_expected.format(attr='aa', env=pp1),
        config_error_mc_required_current_env_expected.format(attr='aa', env=prod1),
    )
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_required_env_expected_ex % dict(ww='were', num_errors=2, err='errors')


def test_attribute_mc_required_default_all_overridden():
    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        # TODO: This should actually not be allowed, it does not make sense!
        cr.setattr('aa?', default=1 + MC_REQUIRED, pp="hello", prod="hi")

    assert cr.aa == "hi"


def test_attribute_mc_required_args_partial_set_in_init_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, aa=MC_REQUIRED):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('aa', prod=aa)
            self.setattr('b', default=17 + MC_REQUIRED, prod=2)

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


# MC_TODO

_attribute_mc_current_env_todo_expected = mc_todo_current_env_expected.format(attr='aa', env=prod1)
_attribute_mc_todo_other_env_expected = mc_todo_other_env_expected.format(attr='aa', env=prod1)


# MC_TODO - Not Allowed for Current Env

_attribute_mc_todo_env_expected_ex = """There was 1 error when defining item: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_env(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('aa?', prod="abc" + MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    print(_sout)
    assert ce(errorline, _attribute_mc_current_env_todo_expected) in serr
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_env_expected_ex
    assert total_msg(1) in str(exinfo.value)


_attribute_mc_todo_default_expected_ex = """There was 1 error when defining item: {
    "__class__": "ConfigRoot #as: 'ConfigRoot', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_default(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo) as cr:
            errorline = lineno() + 1
            cr.setattr('aa?', default=MC_TODO.append("abc"), pp="hello")

    _sout, serr = capsys.readouterr()
    assert ce(errorline, _attribute_mc_current_env_todo_expected) in serr
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_default_expected_ex
    assert total_msg(1) in str(exinfo.value)


_attribute_mc_todo_init_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "aa": "MC_TODO"
}""" + already_printed_msg

@mark.parametrize("allow_todo", [False, True])
def test_attribute_mc_todo_init(capsys, allow_todo):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod_pp, mc_allow_todo=allow_todo):
            with ItemWithAA(aa=MC_TODO + MC_TODO) as ci:
                errorline = lineno() + 1
                ci.setattr('aa', pp="hello")

    _sout, serr = capsys.readouterr()
    assert ce(errorline, _attribute_mc_current_env_todo_expected) in serr
    assert replace_ids(str(exinfo.value), False) == _attribute_mc_todo_init_expected_ex
    assert total_msg(1) in str(exinfo.value)
