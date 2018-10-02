# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import fail, raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder, MC_REQUIRED
from multiconf.config_errors import ConfigException, ConfigExcludedAttributeError, ConfigExcludedKeyError
from multiconf.decorators import named_as, nested_repeatables, required
from multiconf.envs import EnvFactory

from .utils.utils import config_error, next_line_num
from .utils.messages import mc_required_expected
from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithAA

from .include_exclude_classes import McSelectOverrideItem, McSelectOverrideItem2


def ce(line_num, serr, *lines):
    assert config_error(__file__, line_num, *lines) in serr


ef = EnvFactory()
dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
dev3 = ef.Env('dev3')
g_dev12 = ef.EnvGroup('g_dev12', dev1, dev2)
g_dev23 = ef.EnvGroup('g_dev23', dev2, dev3)
g_dev13 = ef.EnvGroup('g_dev13', dev1, dev3)
g_dev12_3 = ef.EnvGroup('g_dev12_3', g_dev12, dev3)
pp = ef.Env('pp')
prod = ef.Env('prod')
g_ppr = ef.EnvGroup('g_ppr', pp, prod)


@named_as('ritems')
class ritem(RepeatableConfigItem):
    pass


class anitem(ConfigItem):
    xx = 1

    def is_excluded(self):
        return not bool(self)


class anotheritem(ConfigItem):
    xx = 2

    def is_excluded(self):
        return not bool(self)


def test_exclude_for_configitem_builder_with_mc_required():
    class RepBuilder(ConfigBuilder):
        def mc_build(self):
            ritem(0)
            with ritem(1) as r1:
                r1.mc_select_envs(exclude=[dev1])
            ritem(2)

    @nested_repeatables('ritems')
    class root(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root() as rt:
            with RepBuilder():
                anitem()
                with anotheritem() as ii:
                    ii.mc_select_envs(exclude=[dev1])

    cr = config(dev1).root

    assert len(cr.ritems) == 2

    ri0 = cr.ritems[0]
    assert ri0
    with raises(ConfigExcludedKeyError):
        ri1 = cr.ritems[1]
    ri2 = cr.ritems[2]
    assert ri2

    assert ri0.anitem
    assert not ri0.anitem.is_excluded()
    assert ri0.anitem.xx == 1
    assert ri0.anitem.contained_in == ri0
    assert not ri0.anotheritem
    assert ri0.anotheritem.is_excluded()

    assert ri2.anitem
    assert not ri2.anitem.is_excluded()
    assert ri2.anitem.xx == 1
    assert ri2.anitem.contained_in == ri2
    assert not ri2.anotheritem
    assert ri0.anotheritem.is_excluded()
