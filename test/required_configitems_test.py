# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from .utils.utils import config_error, config_warning, replace_ids, lineno, total_msg, py3_local
from .utils.messages import exception_previous_object_expected_stderr

from .. import ConfigRoot, ConfigItem, ConfigException, ConfigDefinitionException
from ..decorators import required, named_as, nested_repeatables

from ..envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
prod = ef.Env('prod')


def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)


class _BaseItem(ConfigItem):
    def __init__(self, val):
        super(_BaseItem, self).__init__()
        self.val = val


class anitem(_BaseItem): pass
class anotheritem(_BaseItem): pass
class aa(_BaseItem): pass
class bb(_BaseItem): pass
class someitem2(_BaseItem): pass
class someotheritem2(_BaseItem): pass
class efgh(_BaseItem): pass


def test_required_items_for_configroot_as_str():
    @required('anitem, anotheritem')
    class root(ConfigRoot):
        pass

    with root(prod, ef) as cr:
        anitem(1)
        anotheritem(2)
    assert cr.anitem.val == 1
    assert cr.anotheritem.val == 2


def test_required_items_for_configroot_as_args():
    @required('anitem', 'anotheritem')
    class root(ConfigRoot):
        pass

    with root(prod, ef) as cr:
        anitem(1)
        anotheritem(2)
    assert cr.anitem.val == 1
    assert cr.anotheritem.val == 2


def test_required_items_for_configitem_as_str():
    class root(ConfigRoot):
        pass

    @required('aa, bb')
    class item(ConfigItem):
        pass

    with root(prod, ef) as cr:
        with item():
            aa(1)
            bb(2)

    assert cr.item.aa.val == 1
    assert cr.item.bb.val == 2


def test_required_items_for_configitem_as_args():
    class root(ConfigRoot):
        pass

    @required('aa', 'bb')
    class item(ConfigItem):
        pass

    with root(prod, ef) as cr:
        with item():
            aa(1)
            bb(2)

    assert cr.item.aa.val == 1
    assert cr.item.bb.val == 2


def test_required_items_accept_override_of_default():
    class root(ConfigRoot):
        pass

    @required('aa, bb')
    class item(ConfigItem):
        def __init__(self, a, b):
            super(item, self).__init__()
            self.a = a
            self.b = b

        def mc_init(self):
            super(item, self).mc_init()
            aa(self.a)
            bb(self.b)

    with root(prod, ef) as cr:
        with item(a=1, b=1):
            bb(2)

    assert cr.item.aa.val == 1
    assert cr.item.bb.val == 2


def test_required_items_inherited_ok(capsys):
    @required('anitem, anotheritem')
    class root(ConfigRoot):
        pass

    @required('someitem2, someotheritem2')
    class root2(root):
        pass

    with root2(prod, ef) as cr:
        anitem(1)
        anotheritem(2)
        someitem2(3)
        someotheritem2(4)

    assert cr.anitem.val == 1
    assert cr.anotheritem.val == 2
    assert cr.someitem2.val == 3
    assert cr.someotheritem2.val == 4

    # Check that there is no unwanted output
    sout, serr = capsys.readouterr()
    assert sout == ''
    assert serr == ''


def test_required_items_missing_for_configroot(capsys):
    with raises(ConfigException) as exinfo:
        @required('someitem1, someitem2')
        class root(ConfigRoot):
            pass

        with root(prod, ef):
            errorline = lineno()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Missing '@required' items: ['someitem1', 'someitem2']")
    assert total_msg(1) in str(exinfo.value)


def test_required_items_missing_for_configitem(capsys):
    with raises(ConfigException) as exinfo:
        class root(ConfigRoot):
            pass

        @required('abcd, efgh, ijkl')
        class item(ConfigItem):
            pass

        with root(prod, ef):
            with item() as ii:
                errorline = lineno() + 1
                efgh(7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline, "Missing '@required' items: ['abcd', 'ijkl']")


def test_decorator_arg_not_a_valid_identifier_in_required_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @required('a, a-b, b, 99')
        class root(ConfigRoot):
            pass

    assert str(exinfo.value) == "['a-b', '99'] are not valid identifiers"


def test_error_freezing_previous_sibling_missing_required(capsys):
    @required('a')
    class inner(ConfigItem):
        pass

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, ef):
            errorline = lineno() + 1
            inner()
            inner()

    _sout, serr = capsys.readouterr()
    assert serr.startswith(ce(errorline, "Missing '@required' items: ['a']"))
    assert serr.endswith(exception_previous_object_expected_stderr % dict(
        module='required_configitems_test', py3_local=py3_local()))
    assert total_msg(1) in str(exinfo.value)


def test_required_attributes_inherited_redefined(capsys):
    @required('anitem, anotheritem')
    class root(ConfigRoot):
        pass

    errorline = lineno() + 2
    @required('anitem, someotheritem2')
    class root2(root):
        pass

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, "Item name: 'anitem' re-specified as '@required' on class: 'root2', was already inherited from a super class.")
