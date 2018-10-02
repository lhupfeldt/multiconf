# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import os.path

from pytest import raises, mark

from multiconf import mc_config, ConfigItem, ConfigException, ConfigAttributeError, MC_REQUIRED, MC_TODO, McTodoHandling
from multiconf.envs import EnvFactory

from .utils.utils import config_error, config_warning, next_line_num, replace_ids, lines_in, start_file_line
from .utils.messages import already_printed_msg
from .utils.messages import mc_todo_expected, config_error_mc_todo_expected
from .utils.tstclasses import ItemWithAA


_utils = os.path.join(os.path.dirname(__file__), 'utils')


ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp', allow_todo=True)
prod1 = ef1_prod_pp.Env('prod')

ef3_prod_pp_tst_dev = EnvFactory()
dev3 = ef3_prod_pp_tst_dev.Env('dev')
tst3 = ef3_prod_pp_tst_dev.Env('tst')
pp3 = ef3_prod_pp_tst_dev.Env('pp')
prod3 = ef3_prod_pp_tst_dev.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)


_attribute_mc_todo_allowed_env_expected = mc_todo_expected.format(attr='aa', env=prod1, allowed='')
_attribute_mc_todo_not_allowed_env_expected = mc_todo_expected.format(attr='aa', env=prod1, allowed='')


# MC_TODO - Not Allowed for Current Env

_mc_todo_one_error_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "%(env_name)s"
    },
    "aa": "MC_TODO"
}""" + already_printed_msg


def _conf_with(ef, errorline, todo_handling_other, todo_handling_allowed):
    @mc_config(ef)
    def config(root):
        with ItemWithAA() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=MC_TODO, pprd="hello")

    return config.load(todo_handling_other=todo_handling_other, todo_handling_allowed=todo_handling_allowed)


def _conf_init(ef, errorline, todo_handling_other, todo_handling_allowed):
    @mc_config(ef)
    def config(root):
        with ItemWithAA(aa=MC_TODO) as ci:
            errorline[0] = next_line_num()
            ci.setattr('aa', pprd="hello")

    return config.load(todo_handling_other=todo_handling_other, todo_handling_allowed=todo_handling_allowed)


@mark.parametrize("todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_get_config_allowed_allow_invalid(capsys, todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_with(ef, errorline, todo_handling_other=McTodoHandling.ERROR, todo_handling_allowed=todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd, allow_todo=True)
    _ = config(prod, allow_todo=True)


@mark.parametrize("todo_handling_allowed", [McTodoHandling.ERROR])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_error(capsys, todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    assert todo_handling_allowed == McTodoHandling.ERROR
    with raises(ConfigException) as exinfo:
        _conf_with(ef, errorline, todo_handling_other=McTodoHandling.ERROR, todo_handling_allowed=todo_handling_allowed)

    _sout, serr = capsys.readouterr()

    assert serr == ce(errorline[0], _attribute_mc_todo_not_allowed_env_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


@mark.parametrize("todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_init_get_config_allowed_allow_invalid(capsys, todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_init(ef, errorline, todo_handling_other=McTodoHandling.ERROR, todo_handling_allowed=todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd, allow_todo=True)
    _ = config(prod, allow_todo=True)


@mark.parametrize("todo_handling_allowed", [McTodoHandling.ERROR])
def test_attribute_mc_todo_allowed_all_envs_set_in_init_error(capsys, todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    assert todo_handling_allowed == McTodoHandling.ERROR
    with raises(ConfigException) as exinfo:
        _conf_init(ef, errorline, todo_handling_other=McTodoHandling.ERROR, todo_handling_allowed=todo_handling_allowed)

    _sout, serr = capsys.readouterr()

    assert serr == ce(errorline[0], _attribute_mc_todo_not_allowed_env_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


# --- Not allowed on get config ---

@mark.parametrize("todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_get_config_not_allowed_allow_invalid(capsys, todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_with(ef, errorline, todo_handling_other=McTodoHandling.ERROR, todo_handling_allowed=todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd)

    with raises(ConfigException) as exinfo:
        _ = config(prod)


@mark.parametrize("todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_init_get_config_not_allowed_allow_invalid(capsys, todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_init(ef, errorline, todo_handling_other=McTodoHandling.ERROR, todo_handling_allowed=todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd)

    with raises(ConfigException) as exinfo:
        _ = config(prod)


@mark.parametrize("todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_get_config_not_allowed_allow_invalid_unknown(capsys, todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    @mc_config(ef)
    def config(_):
        with ConfigItem() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=MC_TODO, pprd="hello", mc_set_unknown=True)

    config.load(todo_handling_allowed=todo_handling_allowed)

    _sout, serr = capsys.readouterr()

    if todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd)

    with raises(ConfigException) as exinfo:
        _ = config(prod)


_continuing_with_invalid_conf = ". Continuing with invalid configuration!"
_attribute_mc_current_env_todo_allowed_expected = _attribute_mc_todo_not_allowed_env_expected + _continuing_with_invalid_conf

@mark.parametrize("todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_env_allowed_current_env_access_error(capsys, todo_handling_allowed):
    """Test that accessing an MC_TODO value after loading results in an exception"""
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    @mc_config(ef)
    def config(_):
        with ItemWithAA() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=MC_TODO, pprd="hello")

    config.load(todo_handling_allowed=todo_handling_allowed)

    _sout, serr = capsys.readouterr()

    if todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    cr = config(pprd).ItemWithAA
    assert cr.aa == "hello"

    cr = config(prod, allow_todo=True).ItemWithAA
    with raises(ConfigAttributeError) as exinfo:
        print(cr.aa)

    assert "has no attribute 'aa'" in str(exinfo.value)
    assert "Trying got get MC_TODO" in str(exinfo.value)


def test_bad_handling_arg_allowed():
    @mc_config(ef1_prod_pp)
    def config(_):
        pass

    with raises(ConfigException) as exinfo:
        config.load(todo_handling_allowed=True)

    exp = "'todo_handling_allowed' arg must be instance of 'McTodoHandling'; found type 'bool': True"
    assert str(exinfo.value) == exp


def test_bad_handling_arg_other():
    @mc_config(ef1_prod_pp)
    def config(_):
        pass

    with raises(ConfigException) as exinfo:
        config.load(todo_handling_other=False)

    exp = "'todo_handling_other' arg must be instance of 'McTodoHandling'; found type 'bool': False"
    assert str(exinfo.value) == exp
