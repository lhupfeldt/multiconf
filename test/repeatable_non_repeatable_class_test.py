# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict
# pylint: disable=E0611
from pytest import fail

from .. import ConfigRoot, ConfigItem, RepeatableConfigItem, AbstractConfigItem, MC_REQUIRED
from ..decorators import nested_repeatables, named_as, required
from ..envs import EnvFactory

from .utils.tstclasses import RootWithAA, RootWithAABB, ItemWithAA, ItemWithAABB


ef_pp_prod = EnvFactory()
pp = ef_pp_prod.Env('pp')
prod = ef_pp_prod.Env('prod')


@named_as('children')
class rchild(RepeatableConfigItem):
    def __init__(self, name, aa=None, bb=None):
        super(rchild, self).__init__(mc_key=name)
        self.name = name
        self.aa = aa
        self.bb = bb


class anitem(ConfigItem):
    xx = 1


@required('anitem')
@nested_repeatables('children')
class MyItemBase(AbstractConfigItem):
    def __init__(self, mc_key=None, mc_include=None, mc_exclude=None):
        super(MyItemBase, self).__init__(mc_key=mc_key, mc_include=mc_include, mc_exclude=mc_exclude)
        self.aa = MC_REQUIRED


@named_as('myitem')
class MyItem(ConfigItem, MyItemBase):
    def __init__(self, mc_key=None):
        super(MyItem, self).__init__()

@named_as('myitems')
class MyItems(RepeatableConfigItem, MyItemBase):
    def __init__(self, mc_key=None):
        super(MyItems, self).__init__(mc_key=mc_key)


@nested_repeatables('myitems')
class myroot(ConfigRoot):
    def __init__(self, selected_env, env_factory, mc_json_filter=None, mc_json_fallback=None,
                 mc_allow_todo=False, mc_allow_current_env_todo=False,
                 aa=None):
        super(myroot, self).__init__(
            selected_env=selected_env, env_factory=env_factory, mc_json_filter=mc_json_filter, mc_json_fallback=mc_json_fallback,
            mc_allow_todo=mc_allow_todo, mc_allow_current_env_todo=mc_allow_current_env_todo)


def test_iteritems_item_attributes():
    with myroot(prod, ef_pp_prod) as cr:
        with MyItem() as ci:
            ci.aa = 1
            anitem()

        with MyItems('a') as ci:
            ci.aa = 1
            anitem()

        with MyItems('b') as ci:
            ci.aa = 2
            anitem()

    assert cr.myitem.aa == 1
    assert cr.myitems['a'].aa == 1
    assert cr.myitems['b'].aa == 2
