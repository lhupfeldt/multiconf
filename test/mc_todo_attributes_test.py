# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

import os.path

from pytest import raises, mark, xfail  # pylint: disable=no-name-in-module

from multiconf import mc_config, ConfigItem, ConfigException, MC_REQUIRED, MC_TODO, McTodoHandling
from multiconf.envs import EnvFactory

from .utils.utils import config_error, config_warning, next_line_num, replace_ids, lines_in, start_file_line, py3_tc
from .utils.messages import already_printed_msg
from .utils.messages import mc_required_expected, config_error_mc_required_expected
from .utils.messages import mc_todo_expected, config_error_mc_todo_expected
from .utils.tstclasses import ItemWithAA
from .utils.invalid_values_classes import  McRequiredInInitL1, McRequiredInInitL3


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


def _conf_with(ef, errorline, mc_todo_handling_other, mc_todo_handling_allowed):
    @mc_config(ef, mc_todo_handling_other=mc_todo_handling_other, mc_todo_handling_allowed=mc_todo_handling_allowed)
    def config(root):
        with ItemWithAA() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=MC_TODO, pprd="hello")
    return config


def _conf_init(ef, errorline, mc_todo_handling_other, mc_todo_handling_allowed):
    @mc_config(ef, mc_todo_handling_other=mc_todo_handling_other, mc_todo_handling_allowed=mc_todo_handling_allowed)
    def config(root):
        with ItemWithAA(aa=MC_TODO) as ci:
            errorline[0] = next_line_num()
            ci.setattr('aa', pprd="hello")
    return config


@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_get_config_allowed_allow_invalid(capsys, mc_todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_with(ef, errorline, mc_todo_handling_other=McTodoHandling.ERROR, mc_todo_handling_allowed=mc_todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if mc_todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif mc_todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd, allow_todo=True)
    _ = config(prod, allow_todo=True)


@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.ERROR])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_error(capsys, mc_todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    assert mc_todo_handling_allowed == McTodoHandling.ERROR
    with raises(ConfigException) as exinfo:
        _conf_with(ef, errorline, mc_todo_handling_other=McTodoHandling.ERROR, mc_todo_handling_allowed=mc_todo_handling_allowed)

    _sout, serr = capsys.readouterr()

    assert serr == ce(errorline[0], _attribute_mc_todo_not_allowed_env_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_init_get_config_allowed_allow_invalid(capsys, mc_todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_init(ef, errorline, mc_todo_handling_other=McTodoHandling.ERROR, mc_todo_handling_allowed=mc_todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if mc_todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif mc_todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd, allow_todo=True)
    _ = config(prod, allow_todo=True)


@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.ERROR])
def test_attribute_mc_todo_allowed_all_envs_set_in_init_error(capsys, mc_todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    assert mc_todo_handling_allowed == McTodoHandling.ERROR
    with raises(ConfigException) as exinfo:
        _conf_init(ef, errorline, mc_todo_handling_other=McTodoHandling.ERROR, mc_todo_handling_allowed=mc_todo_handling_allowed)

    _sout, serr = capsys.readouterr()

    assert serr == ce(errorline[0], _attribute_mc_todo_not_allowed_env_expected)
    assert replace_ids(str(exinfo.value), False) == _mc_todo_one_error_expected_ex % dict(env_name='prod')


# --- Not allowed on get config ---

@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_get_config_not_allowed_allow_invalid(capsys, mc_todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_with(ef, errorline, mc_todo_handling_other=McTodoHandling.ERROR, mc_todo_handling_allowed=mc_todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if mc_todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif mc_todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd)

    with raises(ConfigException) as exinfo:
        _ = config(prod)


@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_init_get_config_not_allowed_allow_invalid(capsys, mc_todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    config = _conf_init(ef, errorline, mc_todo_handling_other=McTodoHandling.ERROR, mc_todo_handling_allowed=mc_todo_handling_allowed)
    _sout, serr = capsys.readouterr()

    if mc_todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif mc_todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd)

    with raises(ConfigException) as exinfo:
        _ = config(prod)


@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING])
def test_attribute_mc_todo_allowed_all_envs_set_in_with_get_config_not_allowed_allow_invalid_unknown(capsys, mc_todo_handling_allowed):
    errorline = [None]

    ef = EnvFactory()
    pprd = ef.Env('pprd', allow_todo=True)
    prod = ef.Env('prod', allow_todo=True)

    @mc_config(ef, mc_todo_handling_allowed=mc_todo_handling_allowed)
    def config(_):
        with ConfigItem() as cr:
            errorline[0] = next_line_num()
            cr.setattr('aa', prod=MC_TODO, pprd="hello", mc_set_unknown=True)

    _sout, serr = capsys.readouterr()

    if mc_todo_handling_allowed == McTodoHandling.SILENT:
        assert serr == ''
    elif mc_todo_handling_allowed == McTodoHandling.WARNING:
        assert serr == cw(errorline[0], _attribute_mc_todo_allowed_env_expected)
    else:
        raise Exception("Error in test implementation")

    _ = config(pprd)

    with raises(ConfigException) as exinfo:
        _ = config(prod)


_continuing_with_invalid_conf = ". Continuing with invalid configuration!"
_attribute_mc_current_env_todo_allowed_expected = _attribute_mc_todo_not_allowed_env_expected + _continuing_with_invalid_conf

@mark.parametrize("mc_todo_handling_allowed", [McTodoHandling.SILENT, McTodoHandling.WARNING, McTodoHandling.ERROR])
def test_attribute_mc_todo_env_allowed_current_env_access_error(capsys, mc_todo_handling_allowed):
    xfail("TODO implement test")
    errorline = [None]
    """Test that accessing an MC_TODO value after loading results in an exception"""
    with ItemWithAA(prod1, ef1_prod_pp, mc_allow_current_env_todo=True, mc_todo_handling_allowed=mc_todo_handling_allowed) as cr:
        errorline[0] = next_line_num()
        cr.setattr('aa', prod=MC_TODO, pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline[0], _attribute_mc_current_env_todo_allowed_expected)

    with raises(AttributeError) as exinfo:
        print(cr.aa)

    assert "Attribute 'aa' MC_TODO is undefined for current env " + repr(prod1) in str(exinfo.value)


def test_bad_handling_arg_allowed():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, mc_todo_handling_allowed=True)
        def config(_):
            pass

    exp = "'mc_todo_handling_allowed' arg must be instance of 'McTodoHandling'; found type 'bool': True"
    assert str(exinfo.value) == exp


def test_bad_handling_arg_other():
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod_pp, mc_todo_handling_other=False)
        def config(_):
            pass

    exp = "'mc_todo_handling_other' arg must be instance of 'McTodoHandling'; found type 'bool': False"
    assert str(exinfo.value) == exp
