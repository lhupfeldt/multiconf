# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, replace_ids, replace_ids_builder
from .utils.tstclasses import RootWithName

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, ConfigBuilder, ConfigException, MC_REQUIRED
from ..decorators import nested_repeatables, named_as
from ..envs import EnvFactory


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_pp = EnvFactory()
pp2 = ef2_prod_pp.Env('pp')
prod2 = ef2_prod_pp.Env('prod')


@named_as('xses')
class Xses(RepeatableConfigItem):
    def __init__(self, name=None):
        super(Xses, self).__init__(mc_key=name)
        self.name = name
        self.server_num = None
        self.something = None


@named_as('x_children')
class XChild(RepeatableConfigItem):
    def __init__(self, mc_key=None, a=None):
        super(XChild, self).__init__(mc_key=mc_key)
        self.a = a


_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex = """Nested repeatable from 'build', key: 'server1', value: {
    "__class__": "Xses #as: 'xses', id: 0000, not-frozen",
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
            "__class__": "Xses #as: 'xses', id: 0000",
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

        def build(self):
            for server_num in range(1, self.num_servers+1):
                with Xses(name='server%d' % server_num) as c:
                    c.server_num = server_num
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with raises(ConfigException) as exinfo:
        with Root(prod2, ef2_prod_pp):
            Xses(name='server1')
            with XBuilder():
                pass

    print(str(exinfo.value))
    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex


def test_configbuilder_without_build():
    class ABuilder(ConfigBuilder):
        pass

    with raises(Exception) as exinfo:
        with ConfigRoot(prod2, ef2_prod_pp):
            ABuilder()

    assert str(exinfo.value) == "Can't instantiate abstract class ABuilder with abstract methods build"


_unexpected_repeatable_child_builder_expected_ex = """'r': {
    "__class__": "RepeatableChild #as: 'r', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"""

def test_unexpected_repeatable_child_builder():
    @named_as('r')
    class RepeatableChild(RepeatableConfigItem):
        pass

    class UnexpectedRepeatableChildBuilder(ConfigBuilder):
        def build(self):
            RepeatableChild(mc_key=None)

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod):
            UnexpectedRepeatableChildBuilder()

    assert replace_ids(str(exinfo.value), False) == _unexpected_repeatable_child_builder_expected_ex


_unexpected_repeatable_child_nested_builders_expected_ex = """'arepeatable': {
    "__class__": "RepItem #as: 'arepeatable', id: 0000, not-frozen",
    "name": "a"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ItemWithoutARepeatable'"""

def test_unexpected_repeatable_child_nested_builders():
    @named_as('arepeatable')
    class RepItem(RepeatableConfigItem):
        def __init__(self):
            super(RepItem, self).__init__(mc_key='a')
            self.name = 'a'

    class InnerBuilder(ConfigBuilder):
        def build(self):
            RepItem()

    class MiddleBuilder(ConfigBuilder):
        def build(self):
            InnerBuilder()

    class OuterBuilder(ConfigBuilder):
        def build(self):
            MiddleBuilder()

    class ItemWithoutARepeatable(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod1, ef1_prod):
            with ItemWithoutARepeatable():
                OuterBuilder()

    assert replace_ids(str(exinfo.value), False) == _unexpected_repeatable_child_nested_builders_expected_ex


_configbuilder_child_with_nested_repeatables_undeclared_in_build_expected_ex = """'x_children': {
    "__class__": "XChild #as: 'x_children', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'xses'"""

def test_configbuilder_child_with_nested_repeatables_undeclared_in_build():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()

        def build(self):
            with Xses():
                XChild()

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with raises(ConfigException) as exinfo:
        with Root(prod2, ef2_prod_pp):
            XBuilder()

    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_child_with_nested_repeatables_undeclared_in_build_expected_ex


_configbuilder_child_with_nested_repeatables_undeclared_in_with_expected_ex = """'x_children': {
    "__class__": "XChild #as: 'x_children', id: 0000",
    "a": 10
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'xses'"""

def test_configbuilder_child_with_nested_repeatables_undeclared_in_with():
    class XBuilder(ConfigBuilder):
        def __init__(self):
            super(XBuilder, self).__init__()

        def build(self):
            Xses()

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        aaa = 2

    with raises(ConfigException) as exinfo:
        with Root(prod2, ef2_prod_pp):
            with XBuilder() as xb:
                xb.b = 27
                XChild(a=10)

    assert replace_ids_builder(str(exinfo.value), False) == _configbuilder_child_with_nested_repeatables_undeclared_in_with_expected_ex


def test_configbuilders_repeated_non_repeatable_in_build():
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__()
            self.id = name

    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__()
            self.name = name

        def build(self):
            MiddleItem('middleitem1')
            MiddleItem('middleitem2')
            MiddleItem('middleitem3')

    class OuterItem(ConfigItem):
        pass

    with raises(ConfigException) as exinfo:
        with RootWithName(prod1, ef1_prod) as root:
            root.name = 'myp'
            with OuterItem():
                MiddleBuilder('base1')

    assert replace_ids(str(exinfo.value), False) == "Repeated non repeatable conf item: 'MiddleItem'"

    with raises(ConfigException) as exinfo:
        with RootWithName(prod1, ef1_prod) as root:
            root.name = 'myp'
            MiddleBuilder('base2')

    assert replace_ids(str(exinfo.value), False) == "Repeated non repeatable conf item: 'MiddleItem'"
