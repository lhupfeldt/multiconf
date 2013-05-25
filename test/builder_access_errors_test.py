#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, lineno, replace_ids

from .. import ConfigRoot, ConfigItem, ConfigBuilder, ConfigApiException
from ..decorators import nested_repeatables, named_as, repeat
from ..envs import EnvFactory


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


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


def test_configbuilder_multilevel_nested_items_access_to_contained_in_in_detached_item(capsys):
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
