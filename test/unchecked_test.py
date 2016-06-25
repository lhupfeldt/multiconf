# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises, xfail

from .utils.utils import config_error, lineno, replace_ids, assert_lines_in, already_printed_msg, assert_lines_in

from .. import ConfigRoot, ConfigItem, ConfigException, MC_TODO
from ..decorators import required, unchecked

from ..envs import EnvFactory


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

pp = ef.Env('pp')
prod = ef.Env('prod')


@required('anattr, anotherattr')
@unchecked()
class uitem(ConfigItem):
    def mc_init(self):
        self.setattr('anattr', prod=2, g_dev=2)


class item(uitem):
    pass


def test_required_missing_unchecked_for_configroot():
    @required('anattr, anotherattr')
    @unchecked()
    class root(ConfigRoot):
        def mc_init(self):
            self.setattr('anattr', prod=2, g_dev=2)

    with root(prod, ef) as cr:
        cr.setattr('anattr', pp=1, g_dev=1)
        cr.setattr('anotherattr', prod=2)

    assert cr.anattr == 2
    assert cr.anotherattr == 2

    with root(pp, ef) as cr:
        cr.setattr('anattr', pp=1, g_dev=1)
        cr.setattr('anotherattr', prod=2)

    assert cr.anattr == 1
    with raises(Exception) as exinfo:
        print(cr.anotherattr)

    assert "Attribute 'anotherattr' is undefined for env Env('pp')" in str(exinfo.value)


def test_required_missing_unchecked_for_configitem():
    with ConfigRoot(prod, ef) as cr:
        with uitem() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2)

    assert cr.uitem.anattr == 2
    assert cr.uitem.anotherattr == 2

    with ConfigRoot(dev1, ef) as cr:
        with uitem() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2)

    assert cr.uitem.anattr == 1
    with raises(Exception) as exinfo:
        print(it.anotherattr)

    assert "Attribute 'anotherattr' is undefined for env Env('dev1')" in str(exinfo.value)


def test_required_missing_unchecked_base_for_configitem():
    with ConfigRoot(prod, ef) as cr:
        with item() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2, pp=1, g_dev=0)

    assert cr.item.anattr == 2
    assert cr.item.anotherattr == 2

    with ConfigRoot(dev1, ef) as cr:
        with item() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2, pp=1, g_dev=0)

    assert cr.item.anattr == 1
    assert cr.item.anotherattr == 0


_required_missing_unchecked_super_for_configitem_expected1a = """Attribute: 'anotherattr' did not receive a value for env Env('dev1')"""

_required_missing_unchecked_super_for_configitem_expected1b = """Attribute: 'anotherattr' did not receive a value for env Env('dev2')"""

_required_missing_unchecked_super_for_configitem_expected1_ex = """There were 2 errors when defining item: {
    "__class__": "item #as: 'item', id: 0000",
    "anattr": 2,
    "anotherattr": 2
}""" + already_printed_msg

_required_missing_unchecked_super_for_configitem_expected2_ex = """There was 1 error when defining item: {
    "__class__": "item #as: 'item', id: 0000",
    "anattr": 2,
    "anotherattr": 0
}""" + already_printed_msg

_required_missing_unchecked_super_for_configitem_expected3_ex = """There was 1 error when defining item: {
    "__class__": "item #as: 'item', id: 0000",
    "anattr": 1,
    "anotherattr": 0
}""" + already_printed_msg

def test_required_missing_unchecked_super_for_configitem(capsys):
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with item() as it:
                it.setattr('anattr', pp=1, g_dev=1)
                it.setattr('anotherattr', prod=2, pp=1)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, errorline, serr,
        "^%(lnum)s",
        "^ConfigError: " + _required_missing_unchecked_super_for_configitem_expected1a,
        "^ConfigError: " + _required_missing_unchecked_super_for_configitem_expected1b)
    assert replace_ids(str(exinfo.value), False) == _required_missing_unchecked_super_for_configitem_expected1_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                it.setattr('anotherattr', prod=2, pp=1, g_dev=0)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Attribute: 'anattr' did not receive a value for env Env('pp')")
    assert replace_ids(str(exinfo.value), False) == _required_missing_unchecked_super_for_configitem_expected2_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                it.setattr('anattr', g_dev=1)
                it.setattr('anotherattr', prod=2, pp=1, g_dev=0)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Attribute: 'anattr' did not receive a value for env Env('pp')")
    assert replace_ids(str(exinfo.value), False) == _required_missing_unchecked_super_for_configitem_expected3_ex


def test_unchecked_inheritance():
    @required('q1, q2')
    @unchecked()
    class uitem2(uitem):
        def mc_init(self):
            super(uitem2, self).mc_init()
            self.setattr('q1', prod="Hello", g_dev="Hi")

    class item2(uitem2):
        pass

    xfail("TODO: Test unchecked inheritance")


def test_unchecked_override_attribute_for_configitem():
    @required('anattr, anotherattr')
    @unchecked()
    class uitemwo(ConfigItem):
        def mc_init(self):
            self.setattr('anattr', prod=2, g_dev=2)
            self.override('anotherattr', 111)

    with ConfigRoot(prod, ef) as cr:
        with uitemwo() as it:
            it.setattr('anattr', pp=1, g_dev=1)
            it.setattr('anotherattr', prod=2)

    assert cr.uitemwo.anattr == 2
    assert cr.uitemwo.anotherattr == 111


_unchecked_override_attribute_for_configitem_mc_todo_expected_ex = """There were 4 errors when defining item: {
    "__class__": "citem #as: 'citem', id: 0000",
    "anattr": 2,
    "anotherattr": "MC_TODO"
}""" + already_printed_msg

def test_unchecked_override_attribute_for_configitem_mc_todo(capsys):
    @required('anattr, anotherattr')
    @unchecked()
    class uitemwo(ConfigItem):
        def mc_init(self):
            self.setattr('anattr', prod=2, g_dev=2)
            self.override('anotherattr', self.anotherattr + "/abc")

    class citem(uitemwo):
        pass

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, ef):
            with citem() as it:
                it.setattr('anattr', pp=1, g_dev=1)
                it.setattr('anotherattr', prod=MC_TODO)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    print(serr)
    assert_lines_in(
        __file__, errorline, serr,
        "^ConfigError: Attribute: 'anotherattr' MC_TODO did not receive a value for env Env('dev1')",
        "^ConfigError: Attribute: 'anotherattr' MC_TODO did not receive a value for env Env('dev2')",
        "^ConfigError: Attribute: 'anotherattr' MC_TODO did not receive a value for env Env('pp')",
        "^ConfigError: Attribute: 'anotherattr' MC_TODO did not receive a value for current env Env('prod')",
    )

    assert replace_ids(str(exinfo.value), False) == _unchecked_override_attribute_for_configitem_mc_todo_expected_ex
