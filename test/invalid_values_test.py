# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, replace_ids, assert_lines_in

from .. import ConfigRoot, ConfigItem, ConfigException, MC_REQUIRED
from ..envs import EnvFactory

ef = EnvFactory()

dev2ct = ef.Env('dev2ct')
pp = ef.Env('pp')
prod = ef.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_attribute_mc_required_expected = """Attribute: 'a' MC_REQUIRED did not receive a value for env Env('prod')"""

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
        with ConfigRoot(prod, [dev2ct, prod, pp]) as cr:
            errorline = lineno() + 1
            cr.setattr('a', dev2ct=1, prod="hi", pp=MC_REQUIRED)

    _sout, serr = capsys.readouterr()

    assert_lines_in(
        __file__, errorline, serr,
        "^%(ll)s, dev2ct <type 'int'>",
        "^%(ll)s, prod <type 'str'>",
        "^ConfigError: Found different value types for property 'a' for different envs",
        "^%(ll)s",
        "^ConfigError: Attribute: 'a' MC_REQUIRED did not receive a value for env Env('pp')"
    )
    assert replace_ids(exinfo.value.message, False) == _attribute_mc_required_other_env_different_types_expected_ex


def test_attribute_mc_required_default_all_overridden():
    with ConfigRoot(prod, [prod, pp]) as cr:
        cr.setattr('a', default=MC_REQUIRED, pp="hello", prod="hi")

    assert cr.a == "hi"
