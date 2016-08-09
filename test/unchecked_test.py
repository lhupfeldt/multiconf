# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises, xfail

from .utils.utils import config_error, lineno, replace_ids, assert_lines_in, assert_lines_in
from .utils.messages import already_printed_msg, mc_required_other_env_expected
from .utils.messages import config_error_mc_todo_current_env_expected, config_error_mc_todo_other_env_expected
from .utils.messages import config_error_mc_required_current_env_expected, config_error_mc_required_other_env_expected

from .. import ConfigRoot, ConfigItem, ConfigException, MC_TODO, MC_REQUIRED
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


@unchecked()
class uitem(ConfigItem):
    def __init__(self):
        super(uitem, self).__init__()
        self.anattr = MC_REQUIRED
        self.anotherattr = MC_REQUIRED

    def mc_init(self):
        self.setattr('anattr', prod=2, g_dev=2)


class item(uitem):
    pass


@required('anattr, anotherattr')
@unchecked()
class decorated_uitem(ConfigItem):
    def mc_init(self):
        self.setattr('anattr', prod=2, g_dev=2)


class decorated_item(decorated_uitem):
    pass

            
class anitem(ConfigItem):
    xx = 1


class anotheritem(ConfigItem):
    xx = 2    


def test_required_items_missing_unchecked_for_configroot():
    @required('anitem, anotheritem')
    @unchecked()
    class root(ConfigRoot):
        def mc_init(self):
            anitem()

    with root(prod, ef) as cr:
        anitem()
        anotheritem()

    assert cr.anitem.xx == 1
    assert cr.anotheritem.xx == 2

    with root(pp, ef) as cr:
        anitem()

    assert cr.anitem.xx == 1
    with raises(AttributeError) as exinfo:
        print(cr.anotheritem.xx)

    assert "has no attribute 'anotheritem'" in str(exinfo.value)


def test_mc_required_missing_unchecked_for_configroot():
    @unchecked()
    class root(ConfigRoot):
        def __init__(self, selected_env, env_factory):
            super(root, self).__init__(selected_env, env_factory)
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

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

    assert "Attribute 'anotherattr' MC_REQUIRED is undefined for current env Env('pp')" in str(exinfo.value)


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

    assert "Attribute 'anotherattr' MC_REQUIRED is undefined for current env Env('dev1')" in str(exinfo.value)


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
        config_error_mc_required_other_env_expected.format(attr='anotherattr', env=dev1),
        config_error_mc_required_other_env_expected.format(attr='anotherattr', env=dev2),
    )
    assert replace_ids(str(exinfo.value), False) == _required_missing_unchecked_super_for_configitem_expected1_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                it.setattr('anotherattr', prod=2, pp=1, g_dev=0)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, mc_required_other_env_expected.format(attr='anattr', env=pp))
    assert replace_ids(str(exinfo.value), False) == _required_missing_unchecked_super_for_configitem_expected2_ex

    with raises(ConfigException) as exinfo:
        with ConfigRoot(dev1, ef):
            with item() as it:
                it.setattr('anattr', g_dev=1)
                it.setattr('anotherattr', prod=2, pp=1, g_dev=0)
                errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, mc_required_other_env_expected.format(attr='anattr', env=pp))
    assert replace_ids(str(exinfo.value), False) == _required_missing_unchecked_super_for_configitem_expected3_ex


def test_unchecked_inheritance():
    @required('q1, q2')
    @unchecked()
    class uitem2(uitem):
        def mc_init(self):
            super(uitem2, self).mc_init()
            q1()

    class item2(uitem2):
        pass

    xfail("TODO: Test unchecked inheritance")


def test_unchecked_inheritance():
    @unchecked()
    class uitem2(uitem):
        def __init__(self):
            super(uitem2, self).__init__()
            self.q1 = MC_REQUIRED
            self.q2 = MC_REQUIRED

        def mc_init(self):
            super(uitem2, self).mc_init()
            self.setattr('q1', prod="Hello", g_dev="Hi")

    class item2(uitem2):
        pass

    xfail("TODO: Test unchecked inheritance")


def test_unchecked_override_attribute_for_configitem():
    @unchecked()
    class uitemwo(ConfigItem):
        def __init__(self):
            super(uitemwo, self).__init__()
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED
        
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
    @unchecked()
    class uitemwo(ConfigItem):
        def __init__(self):
            super(uitemwo, self).__init__()
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

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
    assert_lines_in(
        __file__, errorline, serr,
        config_error_mc_todo_other_env_expected.format(attr='anotherattr', env=dev1),
        config_error_mc_todo_other_env_expected.format(attr='anotherattr', env=dev2),
        config_error_mc_todo_other_env_expected.format(attr='anotherattr', env=pp),
        config_error_mc_todo_current_env_expected.format(attr='anotherattr', env=prod),
    )

    assert replace_ids(str(exinfo.value), False) == _unchecked_override_attribute_for_configitem_mc_todo_expected_ex
