# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf.envs import EnvFactory, EnvException

from .utils.utils import config_error, next_line_num


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def test_repeated_direct_env_member(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        ff1 = ef.Env('ff1')
        errorline = next_line_num()
        ff2 = ef.EnvGroup('ff2', ff1, ff1)

    sout, serr = capsys.readouterr()
    assert sout == ''
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "Repeated group member: Env('ff1') in EnvGroup('ff2') {\n\n}"


def test_repeated_direct_group_member(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        gg1 = ef.Env('gg1')
        gg2 = ef.EnvGroup('gg2', gg1)
        errorline = next_line_num()
        gg3 = ef.EnvGroup('gg3', gg2, gg2)

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "Repeated group member: EnvGroup('gg2') {\n   Env('gg1')\n} in EnvGroup('gg3') {\n\n}"


def test_env_or_group_from_string_undefined():
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        ef.env_or_group_from_name("undefined")

    assert str(exinfo.value) == "No such Env or EnvGroup: 'undefined'"


def test_env_name_is_not_a_str(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        _e1 = ef.Env(1)

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "Env: 'name' must be instance of str, found: int"


def test_env_name_is_empty(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        _e1 = ef.Env("")

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "Env: 'name' must not be empty"


def test_env_name_startswith_underscore(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        _e1 = ef.Env("_a")

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "Env: 'name' must not start with '_', got: '_a'"


def test_env_name_eq_default(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        _e1 = ef.Env("default")

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "Env: name 'default' is reserved"


def test_group_name_eq_default(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        e1 = ef.Env("e1")
        _g1 = ef.EnvGroup("default", e1)

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "EnvGroup: name 'default' is reserved"


def test_no_group_members(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        gg2 = ef.EnvGroup('gg')

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "EnvGroup: No group members specified"


def test_group_member_is_not_instanceof_env(capsys):
    with raises(EnvException) as exinfo:
        ef = EnvFactory()
        _g = ef.EnvGroup('gg', 1)

    sout, serr = capsys.readouterr()
    #assert serr == ce(errorline, "TODO")
    assert str(exinfo.value) == "EnvGroup: Group members args must be instance of 'Env' or 'EnvGroup', found: 1"
