# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException, caller_file_line
from ..envs import EnvFactory

from .utils.utils import config_error, lineno, replace_ids, replace_user_file_line_tuple, replace_user_file_line_msg, assert_lines_in
from .utils.messages import already_printed_msg, mc_required_other_env_expected
from .utils.tstclasses import RootWithAA, ItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


class MeSetterRoot(RootWithAA):
    def setme(self, name, **mevalues):
        file_name, line_num = caller_file_line()
        super(MeSetterRoot, self).setattr(name, mc_caller_file_name=file_name, mc_caller_line_num=line_num, **mevalues)

    def overrideme(self, name, val):
        file_name, line_num = caller_file_line()
        super(MeSetterRoot, self).override(name, val, mc_caller_file_name=file_name, mc_caller_line_num=line_num)


class MeSetterItem(ItemWithAA):
    def setme(self, name, **mevalues):
        file_name, line_num = caller_file_line()
        super(MeSetterItem, self).setattr(name, mc_caller_file_name=file_name, mc_caller_line_num=line_num, **mevalues)

    def overrideme(self, name, val):
        file_name, line_num = caller_file_line()
        super(MeSetterItem, self).override(name, val, mc_caller_file_name=file_name, mc_caller_line_num=line_num)


class MeSetterBuilder(ConfigBuilder):
    def build(self):
        pass

    def setme(self, name, **mevalues):
        file_name, line_num = caller_file_line()
        super(MeSetterBuilder, self).setattr(name, mc_caller_file_name=file_name, mc_caller_line_num=line_num, **mevalues)

    def overrideme(self, name, val):
        file_name, line_num = caller_file_line()
        super(MeSetterBuilder, self).override(name, val, mc_caller_file_name=file_name, mc_caller_line_num=line_num)


def test_override_setattr():
    with MeSetterRoot(prod, ef) as cr:
        cr.setme('aa', prod="hi1", pp="hello")
        with MeSetterItem() as ci:
            ci.setme('aa', prod="hi2", pp="hello")
        with MeSetterBuilder() as cb:
            cb.setme('aa', prod="hi3", pp="hello")

    assert cr.aa == "hi1"
    assert ci.aa == "hi2"
    assert cb.aa == "hi3"


_override_setattr1_expected_ex = """There was 1 error when defining item: {
    "__class__": "MeSetterItem #as: 'MeSetterItem', id: 0000",
    "aa": "hi"
}""" + already_printed_msg


def test_override_setattr_error1(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with MeSetterItem() as ci:
                errorline = lineno() + 1
                ci.setme('aa', pros="hello", prod="hi", pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "No such Env or EnvGroup: 'pros'")
    assert replace_ids(str(exinfo.value), False) == _override_setattr1_expected_ex


_override_setattr2_expected_ex = """There was 1 error when defining item: {
    "__class__": "MeSetterItem #as: 'MeSetterItem', id: 0000",
    "aa": "hello"
}""" + already_printed_msg


def test_override_setattr_error2(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with MeSetterItem() as ci:
                errorline = lineno() + 1
                ci.setme('aa', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, mc_required_other_env_expected.format(attr='aa', env=pp))
    assert replace_ids(str(exinfo.value), False) == _override_setattr2_expected_ex


def test_override_override():
    with MeSetterRoot(prod, ef) as cr:
        cr.overrideme('aa', "hello1")
        with MeSetterItem() as ci:
            ci.overrideme('aa', "hello2")
        with MeSetterBuilder() as cb:
            cb.overrideme('aa', "hello3")

    assert cr.aa == "hello1"
    assert ci.aa == "hello2"
    assert cb.aa == "hello3"
