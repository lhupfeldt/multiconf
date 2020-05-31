# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder, ConfigException
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import config_error, replace_ids, replace_ids_builder, local_func, next_line_num
from .utils.tstclasses import ItemWithName, ItemWithAA
from .utils.messages import not_repeatable_in_parent_msg


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_pp = EnvFactory()
pp2 = ef2_prod_pp.Env('pp')
prod2 = ef2_prod_pp.Env('prod')


@named_as('xses')
class X(RepeatableConfigItem):
    def __init__(self, mc_key):
        super().__init__(mc_key=mc_key)
        self.name = mc_key
        self.server_num = None
        self.something = None


@named_as('x_children')
class XChild(RepeatableConfigItem):
    def __init__(self, mc_key, a=None):
        super().__init__(mc_key=mc_key)
        self.a = a


_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex = """Re-used key 'server1' in repeated item <class 'test.builder_definition_errors_test.X'> from 'mc_build' overwrites existing entry in parent:
{
    "__class__": "Root #as: 'Root', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "xses": {
        "server1": {
            "__class__": "X #as: 'xses', id: 0000",
            "name": "server1",
            "server_num": null,
            "something": null
        }
    },
    "mc_ConfigBuilder_XBuilder default-builder": {
        "__class__": "XBuilder #as: 'mc_ConfigBuilder_XBuilder', id: 0000, not-frozen",
        "num_servers": 2
    }
}"""

def test_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item():
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers=2):
            super().__init__()
            self.num_servers = num_servers

        def mc_build(self):
            for server_num in range(1, self.num_servers+1):
                with X('server%d' % server_num) as c:
                    c.server_num = server_num
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with Root():
                X('server1')
                with XBuilder():
                    pass

    print(str(exinfo.value))
    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex


def test_configbuilder_without_build():
    class ABuilder(ConfigBuilder):
        pass

    with raises(Exception) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            ABuilder()

    assert str(exinfo.value) == "Can't instantiate abstract class ABuilder with abstract methods mc_build" or \
        str(exinfo.value) == "Can't instantiate abstract class ABuilder with abstract method mc_build"  # Python 3.9

def test_unexpected_repeatable_child_builder():
    @named_as('r')
    class RepeatableChild(RepeatableConfigItem):
        pass

    class UnexpectedRepeatableChildBuilder(ConfigBuilder):
        def mc_build(self):
            RepeatableChild(mc_key=None)

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ConfigItem():
                UnexpectedRepeatableChildBuilder()

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='r', repeatable_cls="<class 'test.builder_definition_errors_test.%(local_func)sRepeatableChild'>" % dict(local_func=local_func()),
        ci_named_as='ConfigItem', ci_cls="<class 'multiconf.multiconf.ConfigItem'>")
    assert replace_ids(str(exinfo.value), False) == exp


@named_as('arepeatable')
class RepItem(RepeatableConfigItem):
    def __new__(cls):
        super().__new__(cls, mc_key='a')

    def __init__(self):
        super().__init__(mc_key='a')
        self.name = 'a'


def test_unexpected_repeatable_child_nested_builders_with():
    class InnerBuilder(ConfigBuilder):
        def mc_build(self):
            print("InnerBuilder.mc_build", self._mc_where, self._mc_contained_in._mc_where)
            with RepItem():
                pass

    class MiddleBuilder(ConfigBuilder):
        def mc_build(self):
            print("MiddleBuilder.mc_build", self._mc_where, self._mc_contained_in._mc_where)
            with InnerBuilder():
                pass

    class OuterBuilder(ConfigBuilder):
        def mc_build(self):
            print("OuterBuilder.mc_build", self._mc_where, self._mc_contained_in._mc_where)
            with MiddleBuilder():
                pass

    class ItemWithoutARepeatable(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ItemWithoutARepeatable():
                OuterBuilder()

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='arepeatable',
        repeatable_cls="<class 'test.builder_definition_errors_test.RepItem'>",
        ci_named_as='ItemWithoutARepeatable',
        ci_cls="<class 'test.builder_definition_errors_test.%(local_func)sItemWithoutARepeatable'>" % dict(local_func=local_func()))
    assert replace_ids(str(exinfo.value), False) == exp


def test_unexpected_repeatable_child_nested_builders_no_with():
    class InnerBuilder(ConfigBuilder):
        def mc_build(self):
            print("InnerBuilder.mc_build", self._mc_where, self._mc_contained_in._mc_where)
            RepItem()

    class MiddleBuilder(ConfigBuilder):
        def mc_build(self):
            print("MiddleBuilder.mc_build", self._mc_where, self._mc_contained_in._mc_where)
            InnerBuilder()

    class OuterBuilder(ConfigBuilder):
        def mc_build(self):
            print("OuterBuilder.mc_build", self._mc_where, self._mc_contained_in._mc_where)
            MiddleBuilder()

    class ItemWithoutARepeatable(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ItemWithoutARepeatable():
                OuterBuilder()

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='arepeatable',
        repeatable_cls="<class 'test.builder_definition_errors_test.RepItem'>",
        ci_named_as='ItemWithoutARepeatable',
        ci_cls="<class 'test.builder_definition_errors_test.%(local_func)sItemWithoutARepeatable'>" % dict(local_func=local_func()))
    assert replace_ids(str(exinfo.value), False) == exp


_configbuilder_child_with_nested_repeatables_undeclared_in_build_expected_ex = """'x_children': <class 'test.builder_definition_errors_test.XChild'> is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'xses': <class 'test.builder_definition_errors_test.X'>"""

def test_configbuilder_child_with_nested_repeatables_undeclared_in_build():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            with X('tada'):
                XChild('first_child')

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with Root():
                XBuilder()

    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_child_with_nested_repeatables_undeclared_in_build_expected_ex


def test_configbuilder_child_with_nested_repeatables_undeclared_in_with():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            X('tada')

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with Root():
                with XBuilder() as xb:
                    XChild('first_child', a=10)

    exp = """'x_children': <class 'test.builder_definition_errors_test.XChild'> is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'xses': <class 'test.builder_definition_errors_test.X'>"""
    assert replace_ids_builder(str(exinfo.value), False) == exp


def test_configbuilders_repeated_non_repeatable_in_build():
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super().__init__()
            self.id = name

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def mc_build(self):
            MiddleItem('middleitem1')
            MiddleItem('middleitem2')
            MiddleItem('middleitem3')

    class OuterItem(ConfigItem):
        pass

    exp = "Repeated non repeatable conf item: 'MiddleItem': <class 'test.builder_definition_errors_test.%(local_func)sMiddleItem'>" % dict(local_func=local_func())

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ItemWithName() as root:
                root.name = 'myp'
                with OuterItem():
                    MiddleBuilder('base1')

    assert replace_ids(str(exinfo.value), False) == exp

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ItemWithName() as root:
                root.name = 'myp'
                MiddleBuilder('base2')

    assert replace_ids(str(exinfo.value), False) == exp


def test_configbuilder_undeclared_repeatable_child(capsys):
    """Test that a repeatable declared in 'with' raises an error when assigned under an item from 'mc_build' which has not declared the repeatable."""
    class YBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            Y('y1')

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    class Y(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)

    @named_as('y_children')
    class YChild(RepeatableConfigItem):
        def __init__(self, mc_key, a):
            super().__init__(mc_key=mc_key)
            self.a = a

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(_):
            with ItemWithYs():
                with YBuilder() as yb1:
                    YChild(mc_key=None, a=10)

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='y_children', repeatable_cls="<class 'test.builder_definition_errors_test.%(local_func)sYChild'>" % dict(local_func=local_func()),
        ci_named_as='ys', ci_cls="<class 'test.builder_definition_errors_test.%(local_func)sY'>"% dict(local_func=local_func()))

    assert replace_ids(str(exinfo.value), False) == exp


_configbuilder_repeated = """Re-used key 'aa' in repeated item <class 'test.builder_definition_errors_test.%(local_func)sXBuilder'> overwrites existing entry in parent:
{
    "__class__": "Root #as: 'Root', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "pp"
    },
    "mc_ConfigBuilder_XBuilder aa": {
        "__class__": "XBuilder #as: 'mc_ConfigBuilder_XBuilder', id: 0000, not-frozen"
    }
}"""

def test_configbuilder_repeated():
    class XBuilder(ConfigBuilder):
        def __init__(self, mc_key):
            super().__init__(mc_key)

        def mc_build(self):
            pass

    class Root(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp, load_now=True)
        def config(_):
            with Root():
                XBuilder('aa')
                XBuilder('aa')

    print(str(exinfo.value))
    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_repeated % dict(local_func=local_func())


def test_configbuilder_repeated_in_mc_init():
    class XBuilder(ConfigBuilder):
        def __init__(self, mc_key):
            super().__init__(mc_key)

        def mc_build(self):
            pass

    class Root(ConfigItem):
        def mc_init(self):
            # This redefinition is ignored as it it interpreted as a defult value
            XBuilder('aa')

    @mc_config(ef2_prod_pp, load_now=True)
    def config(_):
        with Root():
            XBuilder('aa')




_assign_on_built_item_after_it_is_built_expected_ex = """There was 1 error when defining item: {
    "__class__": "Y #as: 'y', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "something": null
}
Check already printed error messages."""

def test_assign_on_built_item_after_it_is_built(capsys):
    errorline = [None]

    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()

        def mc_build(self):
            Y()

    @named_as('y')
    class Y(ConfigItem):
        def __init__(self):
            super().__init__()
            self.something = None

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config(root):
            with YBuilder():
                pass

            errorline[0] = next_line_num()
            root.y.something = 1  # TODO? Should getattr finalize previous object

    _sout, serr = capsys.readouterr()
    exp = "Trying to set attribute 'something'. Setting attributes is not allowed after item is 'frozen' (with 'scope' is exited)."
    assert serr == ce(errorline[0], exp)
    assert replace_ids(str(exinfo.value), False) == _assign_on_built_item_after_it_is_built_expected_ex


_assign_on_proxied_built_item_child_after_freeze_expected_ex = """There was 1 error when defining item: {
    "__class__": "ItemWithAA #as: 'ItemWithAA', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 17
}
Check already printed error messages."""

def test_assign_and_assign_on_proxied_built_item_child_after_freeze(capsys):
    """This will go through the proxy object"""
    errorline = [None]

    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()

        def mc_build(self):
            Y()

    @named_as('y')
    class Y(ConfigItem):
        def __init__(self):
            super().__init__()
            self.something = None

    # Test assignment error
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config1(root):
            with YBuilder():
                ItemWithAA(17)
            errorline[0] = next_line_num()
            root.y.ItemWithAA.aa = 1

    _sout, serr = capsys.readouterr()
    exp = "Trying to set attribute 'aa'. Setting attributes is not allowed after item is 'frozen' (with 'scope' is exited)."
    assert serr == ce(errorline[0], exp)
    assert replace_ids(str(exinfo.value), False) == _assign_on_proxied_built_item_child_after_freeze_expected_ex

    # Test setattr error
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod, load_now=True)
        def config2(root):
            with YBuilder():
                ItemWithAA(17)
            errorline[0] = next_line_num()
            root.y.ItemWithAA.setattr('aa', default=1)

    _sout, serr = capsys.readouterr()
    exp = "Trying to set attribute 'aa'. Setting attributes is not allowed after item is 'frozen' (with 'scope' is exited)."
    assert serr == ce(errorline[0], exp)
    assert replace_ids(str(exinfo.value), False) == _assign_on_proxied_built_item_child_after_freeze_expected_ex
