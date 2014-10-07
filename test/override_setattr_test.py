# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, replace_ids, replace_user_file_line_tuple, replace_user_file_line_msg, assert_lines_in

from .. import ConfigRoot, ConfigItem, ConfigException, caller_file_line
from ..envs import EnvFactory

ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


_override_setattr1_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "MeSetter #as: 'MeSetter', id: 0000, not-frozen",
    "a": "hi"
}"""


_override_setattr2_expected_ex = """There were 1 errors when defining attribute 'a' on object: {
    "__class__": "MeSetter #as: 'MeSetter', id: 0000, not-frozen",
    "a": "hello"
}"""


class MeSetter(ConfigItem):
    def setme(self, name, **mevalues):
        file_name, line_num = caller_file_line()
        super(MeSetter, self).setattr(name, mc_caller_file_name=file_name, mc_caller_line_num=line_num, **mevalues)


def test_override_setattr1(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with MeSetter() as ci:
                errorline = lineno() + 1
                ci.setme('a', pros="hello", prod="hi", pp="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "No such Env or EnvGroup: 'pros'")
    assert replace_ids(exinfo.value.message, False) == _override_setattr1_expected_ex


def test_override_setattr2(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with MeSetter() as ci:
                errorline = lineno() + 1
                ci.setme('a', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Attribute: 'a' did not receive a value for env Env('pp')")
    assert replace_ids(exinfo.value.message, False) == _override_setattr2_expected_ex
