# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder, ConfigApiException
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num, replace_ids


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)

ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


def test_configbuilder_multilevel_nested_items_access_to_contained_in_in_wrong_scope(capsys):
    errorline = [None]

    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()
            self.start = start
            self.number = self.contained_in.aaa

        def mc_build(self):
            for num in range(self.start, self.start + self.number):
                with Y('server%d' % num, server_num=num) as c:
                    c.setattr('something', prod=1, pp=2)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    @nested_repeatables('y_children')
    class Y(RepeatableConfigItem):
        def __init__(self, mc_key, server_num):
            super().__init__(mc_key=mc_key)
            self.server_num = server_num
            self.something = None

    @named_as('y_children')
    class YChild(RepeatableConfigItem):
        def __init__(self, mc_key, a):
            super().__init__(mc_key=mc_key)
            self.a = a

    with raises(ConfigApiException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with ItemWithYs():
                with YBuilder() as yb1:
                    with YChild(mc_key=None, a=10) as y1:
                        errorline[0] = next_line_num()
                        _item = y1.contained_in

    _sout, serr = capsys.readouterr()
    exp = "Use of 'contained_in' in not allowed in object while under the 'with' statement of a ConfigBuilder. The final containment is still unknown."
    assert serr == ce(errorline[0], exp)
    assert replace_ids(str(exinfo.value), False) == exp


def test_configbuilder_multilevel_nested_items_access_to_contained_in_through_direct_built_item_ref(capsys):
    yc10 = [None]

    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()
            self.start = start

        def mc_build(self):
            pass

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    @nested_repeatables('y_children', 'ys')
    class Y(RepeatableConfigItem):
        def __init__(self, mc_key, name, server_num):
            super().__init__(mc_key=mc_key)
            self.name = name
            self.server_num = server_num

    @named_as('y_children')
    class YChild(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=None)
            self.a = mc_key

    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithYs() as item:
            with YBuilder() as yb1:
                yc10[0] = YChild(mc_key=10)

    item = config(prod).ItemWithYs

    with raises(ConfigApiException) as exinfo:
        errorline = next_line_num()
        yc10[0].contained_in

    sout, serr = capsys.readouterr()
    exp = "Use of 'contained_in' in not allowed through direct reference to an item from 'with' statement of a ConfigBuilder. Containment is unknown."
    assert serr == ce(errorline, exp)
    assert sout == ''
    assert replace_ids(str(exinfo.value), False) == exp
