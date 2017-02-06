# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises, xfail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder, ConfigException, MC_REQUIRED
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import config_error, replace_ids, replace_ids_builder, py3_local
from .utils.tstclasses import ItemWithName
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
        super(X, self).__init__(mc_key=mc_key)
        self.name = mc_key
        self.server_num = None
        self.something = None


@named_as('x_children')
class XChild(RepeatableConfigItem):
    def __init__(self, mc_key, a=None):
        super(XChild, self).__init__(mc_key=mc_key)
        self.a = a


_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex = """Nested repeatable from 'build', key: 'server1', value: {
    "__class__": "X #as: 'xses', id: 0000, not-frozen",
    "name": "server1",
    "num_servers": 2,
    "server_num": 1,
    "something": 1
} overwrites existing entry in parent: {
    "__class__": "Root #as: 'Root', id: 0000, not-frozen",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "xses": {
        "server1": {
            "__class__": "X #as: 'xses', id: 0000",
            "name": "server1",
            "server_num": null,
            "something": null
        }
    },
    "XBuilder.builder.0000": {
        "__class__": "XBuilder #as: 'XBuilder.builder.0000', id: 0000, not-frozen",
        "num_servers": 2
    }
}"""

def test_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item():
    class XBuilder(ConfigBuilder):
        def __init__(self, num_servers=2):
            super(XBuilder, self).__init__()
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
        @mc_config(ef2_prod_pp)
        def _(_):
            with Root():
                X('server1')
                with XBuilder():
                    pass

    xfail("TODO") 
    print(str(exinfo.value))
    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex


def test_configbuilder_without_build():
    class ABuilder(ConfigBuilder):
        pass

    with raises(Exception) as exinfo:
        @mc_config(ef2_prod_pp)
        def _(_):
            ABuilder()

    assert str(exinfo.value) == "Can't instantiate abstract class ABuilder with abstract methods mc_build"


def test_unexpected_repeatable_child_builder():
    @named_as('r')
    class RepeatableChild(RepeatableConfigItem):
        pass

    class UnexpectedRepeatableChildBuilder(ConfigBuilder):
        def mc_build(self):
            RepeatableChild(mc_key=None)

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ConfigItem():
                UnexpectedRepeatableChildBuilder()

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='r', repeatable_cls="<class 'test.builder_definition_errors_test.%(py3_local)sRepeatableChild'>" % dict(py3_local=py3_local()),
        ci_named_as='ConfigItem', ci_cls="<class 'multiconf.multiconf.ConfigItem'>")
    assert replace_ids(str(exinfo.value), False) == exp


def test_unexpected_repeatable_child_nested_builders():
    @named_as('arepeatable')
    class RepItem(RepeatableConfigItem):
        def __init__(self):
            super(RepItem, self).__init__(mc_key='a')
            self.name = 'a'

    class InnerBuilder(ConfigBuilder):
        def mc_build(self):
            RepItem()

    class MiddleBuilder(ConfigBuilder):
        def mc_build(self):
            InnerBuilder()

    class OuterBuilder(ConfigBuilder):
        def mc_build(self):
            MiddleBuilder()

    class ItemWithoutARepeatable(ConfigItem):
        pass

    xfail("TODO")
    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ItemWithoutARepeatable():
                OuterBuilder()

    exp = not_repeatable_in_parent_msg.format(
        repeatable_cls_key='arepeatable', repeatable_cls="<class 'test.builder_definition_errors_test.RepItem'>",
        ci_named_as='ItemWithoutARepeatable', ci_cls="<class 'test.builder_definition_errors_test.ItemWithoutARepeatable'>")
    assert replace_ids(str(exinfo.value), False) == exp


_configbuilder_child_with_nested_repeatables_undeclared_in_build_expected_ex = """'x_children': {
    "__class__": "XChild #as: 'x_children', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'xses'"""

def test_configbuilder_child_with_nested_repeatables_undeclared_in_build():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()

        def mc_build(self):
            with X('tada'):
                XChild('first_child')

    @nested_repeatables('xses')
    class Root(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp)
        def _(_):
            with Root():
                XBuilder()

    xfail("TODO")
    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_child_with_nested_repeatables_undeclared_in_build_expected_ex


def test_configbuilder_child_with_nested_repeatables_undeclared_in_with():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()

        def mc_build(self):
            X('tada')

    @nested_repeatables('xses')
    class Root(ConfigItem):
        aaa = 2

    with raises(ConfigException) as exinfo:
        @mc_config(ef2_prod_pp)
        def _(_):
            with Root():
                with XBuilder() as xb:
                    XChild('first_child', a=10)

    exp = """'x_children': <class 'test.builder_definition_errors_test.XChild'> is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'xses': <class 'test.builder_definition_errors_test.X'>"""
    assert replace_ids_builder(str(exinfo.value), False) == exp


def test_configbuilders_repeated_non_repeatable_in_build():
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__()
            self.id = name

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__()
            self.name = name

        def mc_build(self):
            MiddleItem('middleitem1')
            MiddleItem('middleitem2')
            MiddleItem('middleitem3')

    class OuterItem(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ItemWithName() as root:
                root.name = 'myp'
                with OuterItem():
                    MiddleBuilder('base1')

    exp = "Repeated non repeatable conf item: 'MiddleItem': <class 'test.builder_definition_errors_test.%(py3_local)sMiddleItem'>" % dict(py3_local=py3_local())

    assert replace_ids(str(exinfo.value), False) == exp

    with raises(ConfigException) as exinfo:
        @mc_config(ef1_prod)
        def _(_):
            with ItemWithName() as root:
                root.name = 'myp'
                MiddleBuilder('base2')

    assert replace_ids(str(exinfo.value), False) == exp
