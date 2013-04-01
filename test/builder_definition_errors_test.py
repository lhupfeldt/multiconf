#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils import config_error, lineno, replace_ids, replace_ids_builder

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigApiException, ConfigException
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


def test_configbuilder_multilevel_nested_items_access_to_contained_in_in_wrong_scope(capsys):
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super(YBuilder, self).__init__()
            self.start = start
            self.number = self.contained_in.aaa

        def build(self):
            for num in xrange(self.start, self.start + self.number):
                with Ys(name='server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    @repeat()
    class Ys(ConfigItem):
        def __init__(self, **kwarg):
            super(Ys, self).__init__(**kwarg)

    @named_as('y_children')
    @repeat()
    class YChild(ConfigItem):
        pass

    with raises(ConfigApiException) as exinfo:
        with ConfigRoot(prod, [prod, pp]):
            with ItemWithYs():
                with YBuilder() as yb1:
                    yb1.b = 27
                    with YChild(a=10) as y1:
                        errorline = lineno() + 1
                        _item = y1.contained_in

    _sout, serr = capsys.readouterr()
    # assert serr == ce(errorline, '')
    assert replace_ids(exinfo.value.message, False) == "Use of 'contained_in' in not allowed in object while under a ConfigBuilder"


_test_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex = """Nested repeatable from 'build', key: 'server1', value: {
    "__class__": "Xses #as: 'xses', id: 0000", 
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
        "__class__": "XBuilder #as: 'XBuilder.builder.0000', id: 0000", 
        "num_servers": 2, 
        "xses": {
            "server1": {
                "__class__": "Xses #as: 'xses', id: 0000", 
                "name": "server1", 
                "server_num": 1, 
                "something": 1, 
                "num_servers": 2
            }, 
            "server2": {
                "__class__": "Xses #as: 'xses', id: 0000", 
                "name": "server2", 
                "server_num": 2, 
                "something": 1, 
                "num_servers": 2
            }
        }
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

    assert replace_ids_builder(exinfo.value.message, False) == _test_configbuilder_override_nested_repeatable_overwrites_parent_repeatable_item_expected_ex


def test_configbuilder_without_build():
    class ABuilder(ConfigBuilder):
        pass

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, [prod, pp]):
            ABuilder()

    assert exinfo.value.message == "AbstractNotImplemented"
