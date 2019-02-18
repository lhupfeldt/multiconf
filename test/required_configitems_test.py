# Copyright (c) 2016 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigException, ConfigDefinitionException
from multiconf.decorators import required
from multiconf.envs import EnvFactory

from .utils.utils import config_error, config_warning, next_line_num, line_num, total_msg, local_func
from .utils.messages import exception_previous_object_expected_stderr


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


def cw(line_num, *lines):
    return config_warning(__file__, line_num, *lines)


class _BaseItem(ConfigItem):
    def __init__(self, val):
        super().__init__()
        self.val = val


class anitem(_BaseItem): pass
class anotheritem(_BaseItem): pass
class aa(_BaseItem): pass
class bb(_BaseItem): pass
class someitem2(_BaseItem): pass
class someotheritem2(_BaseItem): pass
class efgh(_BaseItem): pass


def test_required_items_for_configroot_as_args():
    @required('anitem', 'anotheritem')
    class root(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            anitem(1)
            anotheritem(2)

    cr = config(prod).root
    assert cr.anitem.val == 1
    assert cr.anotheritem.val == 2


def test_required_items_for_configitem_as_args():
    class root(ConfigItem):
        pass

    @required('aa', 'bb')
    class item(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root():
            with item():
                aa(1)
                bb(2)

    cr = config(prod).root
    assert cr.item.aa.val == 1
    assert cr.item.bb.val == 2


def test_required_items_accept_override_of_default():
    class root(ConfigItem):
        pass

    @required('aa', 'bb')
    class item(ConfigItem):
        def __init__(self, a, b):
            super().__init__()
            self.a = a
            self.b = b

        def mc_init(self):
            super().mc_init()
            aa(self.a)
            bb(self.b)

    @mc_config(ef, load_now=True)
    def config(_):
        with item(a=1, b=1):
            bb(2)

    cr = config(prod)
    assert cr.item.aa.val == 1
    assert cr.item.bb.val == 2


def test_required_items_inherited_ok(capsys):
    @required('anitem', 'anotheritem')
    class root(ConfigItem):
        pass

    @required('someitem2', 'someotheritem2')
    class root2(root):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root2():
            anitem(1)
            anotheritem(2)
            someitem2(3)
            someotheritem2(4)

    cr = config(prod).root2
    assert cr.anitem.val == 1
    assert cr.anotheritem.val == 2
    assert cr.someitem2.val == 3
    assert cr.someotheritem2.val == 4

    # Check that there is no unwanted output
    sout, serr = capsys.readouterr()
    assert sout == ''
    assert serr == ''


def test_required_items_missing_for_configroot(capsys):
    errorline = [None]

    @required('someitem1', 'someitem2')
    class root(ConfigItem):
        pass

    @mc_config(ef)
    def config(_):
        with root():
            errorline[0] = line_num()

    with raises(ConfigException) as exinfo:
        config.load()

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], "Missing '@required' items: ['someitem1', 'someitem2']")
    assert total_msg(1) in str(exinfo.value)


def test_required_items_missing_for_configitem(capsys):
    errorline = [None]

    with raises(ConfigException) as exinfo:
        class root(ConfigItem):
            pass

        @required('abcd', 'efgh', 'ijkl')
        class item(ConfigItem):
            pass

        @mc_config(ef, load_now=True)
        def config(_):
            with root():
                with item():
                    errorline[0] = next_line_num()
                    efgh(7)

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], "Missing '@required' items: ['abcd', 'ijkl']")


def test_decorator_arg_not_a_valid_identifier_in_required_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @required('a', 'a-b', 'b', '99')
        class root(ConfigItem):
            pass

    assert str(exinfo.value) == "['a-b', '99'] are not valid identifiers."

    with raises(ConfigDefinitionException) as exinfo:
        @required('x, y')
        class root(ConfigItem):
            pass

    assert str(exinfo.value) == "'x, y' is not a valid identifier."


def test_error_freezing_previous_sibling_missing_required(capsys):
    errorline = [None]

    @required('a')
    class inner(ConfigItem):
        pass

    with raises(Exception) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with ConfigItem():
                errorline[0] = next_line_num()
                inner()
                ConfigItem()

    _sout, serr = capsys.readouterr()
    # TODO errorline
    print(serr)
    assert "Missing '@required' items: ['a']" in serr
    assert serr.endswith(exception_previous_object_expected_stderr % dict(
        module='required_configitems_test', local_func=local_func()))
    assert total_msg(1) in str(exinfo.value)


def test_required_attributes_inherited_redefined(capsys):
    @required('anitem', 'anotheritem')
    class root(ConfigItem):
        pass

    errorline = next_line_num() + 1
    @required('anitem', 'someotheritem2')
    class root2(root):
        pass

    _sout, serr = capsys.readouterr()
    assert serr == cw(errorline, "Item name: 'anitem' re-specified as '@required' on class: 'root2', was already inherited from a super class.")
