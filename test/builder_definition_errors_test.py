#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, replace_ids, replace_ids_builder

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigException
from ..decorators import nested_repeatables, named_as, repeat
from ..envs import EnvFactory


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

@named_as('xses')
@repeat()
class Xses(ConfigItem):
    pass


@named_as('x_children')
@repeat()
class XChild(ConfigItem):
    pass


_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex = """Nested repeatable from 'build', key: 'server1', value: {
    "__class__": "Xses #as: 'xses', id: 0000, not-frozen", 
    "name": "server1", 
    "server_num": 1, 
    "something": 1, 
    "num_servers": 2
} overwrites existing entry in parent: {
    "__class__": "Root #as: 'Root', id: 0000, not-frozen", 
    "env": {
        "__class__": "Env", 
        "name": "prod"
    }, 
    "xses": {
        "server1": {
            "__class__": "Xses #as: 'xses', id: 0000", 
            "name": "server1"
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
            super(XBuilder, self).__init__(num_servers=num_servers)

        def build(self):
            for server_num in xrange(1, self.num_servers+1):
                with Xses(name='server%d' % server_num, server_num=server_num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('xses')
    class Root(ConfigRoot):
        pass

    with raises(ConfigException) as exinfo:
        with Root(prod, [prod, pp]):
            Xses(name='server1')
            with XBuilder():
                pass
    
    assert replace_ids_builder(exinfo.value.message, False) == _configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex


def test_configbuilder_without_build():
    class ABuilder(ConfigBuilder):
        pass

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, [prod, pp]):
            ABuilder()

    assert exinfo.value.message == "Can't instantiate abstract class ABuilder with abstract methods build"


_unexpected_repeatable_child_builder_expected_ex = """'r': {
    "__class__": "RepeatableChild #as: 'r', id: 0000, not-frozen"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ConfigRoot'"""

def test_unexpected_repeatable_child_builder():
    @repeat()
    @named_as('r')
    class RepeatableChild(ConfigItem):
        pass
    
    class UnexpectedRepeatableChildBuilder(ConfigBuilder):
        def build(self):
            RepeatableChild()
    
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, valid_envs=[prod]):
            UnexpectedRepeatableChildBuilder()

    assert replace_ids(exinfo.value.message, False) == _unexpected_repeatable_child_builder_expected_ex


_unexpected_repeatable_child_nested_builders_expected_ex = """'arepeatable': {
    "__class__": "RepItem #as: 'arepeatable', id: 0000, not-frozen", 
    "name": "a"
} is defined as repeatable, but this is not defined as a repeatable item in the containing class: 'ItemWithoutARepeatable'"""

def test_unexpected_repeatable_child_nested_builders():
    @repeat()
    @named_as('arepeatable')
    class RepItem(ConfigItem):
        def __init__(self):
            super(RepItem, self).__init__(name='a')

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
        with ConfigRoot(prod, valid_envs=[prod]):
            with ItemWithoutARepeatable():
                OuterBuilder()

    assert replace_ids(exinfo.value.message, False) == _unexpected_repeatable_child_nested_builders_expected_ex


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
        with Root(prod, [prod, pp]):
            XBuilder()

    assert replace_ids_builder(exinfo.value.message, False) == _configbuilder_child_with_nested_repeatables_undeclared_in_build_expected_ex


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
        with Root(prod, [prod, pp]):
            with XBuilder() as xb:
                xb.b = 27
                XChild(a=10)

    assert replace_ids_builder(exinfo.value.message, False) == _configbuilder_child_with_nested_repeatables_undeclared_in_with_expected_ex


def test_configbuilders_repeated_non_repeatable_in_build():
    class MiddleItem(ConfigItem):
        def __init__(self, name):
            super(MiddleItem, self).__init__(id=name)
    
    class MiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MiddleBuilder, self).__init__(name=name)
    
        def build(self):
            MiddleItem('middleitem1')
            MiddleItem('middleitem2')
            MiddleItem('middleitem3')
    
    class OuterItem(ConfigItem):
        pass
    
    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod], name='myp'):
            with OuterItem():
                MiddleBuilder('base1')

    assert replace_ids(exinfo.value.message, False) == "Repeated non repeatable conf item: 'MiddleItem'"

    with raises(ConfigException) as exinfo:
        with ConfigRoot(prod, [prod], name='myp'):
            MiddleBuilder('base2')

    assert replace_ids(exinfo.value.message, False) == "Repeated non repeatable conf item: 'MiddleItem'"
