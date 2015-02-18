# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.


# Test that different ConfigRoots can use different EnvFactories without interference, i.e,
# there is no unintended static information in the envs module

# pylint: disable=E0611
from pytest import raises

from .. import ConfigRoot, ConfigItem, ConfigException
from ..envs import EnvFactory

from .utils.utils import lineno, assert_lines_in, replace_ids


class item(ConfigItem):
    def mc_init(self):
        # TODO
        self.bb = 111


_env_factories_ef1_expected_ex = """There were 3 errors when defining attribute 'aa' on object: {
    "__class__": "item #as: 'item', id: 0000, not-frozen",
    "aa": 1
}"""

def test_env_factories_ef1(capsys):
    ef = EnvFactory()

    dev1 = ef.Env('dev1')
    dev2 = ef.Env('dev2')
    g_dev = ef.EnvGroup('g_dev', dev1, dev2)

    pp = ef.Env('pp')
    prod = ef.Env('prod')

    with ConfigRoot(dev1, ef):
        with item() as it:
            it.setattr('aa', default=13)
    assert it.aa == 13

    with ConfigRoot(dev1, ef):
        with item() as it:
            it.setattr('aa', dev1=1, dev2=2, pp=3, prod=4)
    assert it.aa == 1
    assert it.bb == 111

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                errorline = lineno() + 1
                it.setattr('aa', dev1=1, dev2=2, g_prod=4)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: No such Env or EnvGroup: 'g_prod'",
        "^%(lnum)s",
        "^ConfigError: Attribute: 'aa' did not receive a value for env Env('pp')",
        "^%(lnum)s",
        "^ConfigError: Attribute: 'aa' did not receive a value for env Env('prod')",
    )
    assert replace_ids(str(exinfo.value), False) == _env_factories_ef1_expected_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                errorline = lineno() + 1
                it.setattr('aa', dev1=1, dev2=2, dev3=3, pp=4, prod=5)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: No such Env or EnvGroup: 'dev3'",
    )


_env_factories_ef2_expected_ex = """There were 1 errors when defining attribute 'aa' on object: {
    "__class__": "item #as: 'item', id: 0000, not-frozen",
    "aa": 1
}"""


def test_env_factories_ef2(capsys):
    ef = EnvFactory()

    dev1 = ef.Env('dev1')
    dev2 = ef.Env('dev2')
    dev3 = ef.Env('dev3')
    g_dev = ef.EnvGroup('g_dev', dev1, dev2, dev3)

    pp = ef.Env('pp')
    prod = ef.Env('prod')
    g_prod = ef.EnvGroup('g_prod', pp, prod)

    with ConfigRoot(dev1, ef):
        with item() as it:
            it.setattr('aa', default=13)
    assert it.aa == 13

    with ConfigRoot(dev3, ef):
        with item() as it:
            it.setattr('aa', dev1=1, g_dev=7, g_prod=17)
    assert it.aa == 7
    assert it.bb == 111

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                errorline = lineno() + 1
                it.setattr('aa', dev1=1, dev2=2, g_prod=4)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: Attribute: 'aa' did not receive a value for env Env('dev3')",
    )
    assert replace_ids(str(exinfo.value), False) == _env_factories_ef2_expected_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                errorline = lineno() + 1
                it.setattr('aa', dev1=1, dev2=2, dev3=3, pp=4, pp2=4, prod=5)

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: No such Env or EnvGroup: 'pp2'",
    )
