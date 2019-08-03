# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, AbstractConfigItem, MC_REQUIRED
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory


ef_pp_prod = EnvFactory()
pp = ef_pp_prod.Env('pp')
prod = ef_pp_prod.Env('prod')


@named_as('children')
class rchild(RepeatableConfigItem):
    def __init__(self, name, aa=None, bb=None):
        super().__init__(mc_key=name)
        self.name = name
        self.aa = aa
        self.bb = bb


class anitem(ConfigItem):
    xx = 1


class ConfigItemMiWrapper(ConfigItem):
    def __init__(self, mc_key=None, mc_include=None, mc_exclude=None):
        super().__init__(mc_include=mc_include, mc_exclude=mc_exclude)


@required('anitem')
@nested_repeatables('children')
class MyItemBase(AbstractConfigItem):
    def __init__(self, xx, mc_key=None, mc_include=None, mc_exclude=None):
        super().__init__(mc_key=mc_key, mc_include=mc_include, mc_exclude=mc_exclude)
        self.xx = xx
        self.aa = MC_REQUIRED


@named_as('myitem')
class MyItem(MyItemBase, ConfigItemMiWrapper):
    def __init__(self, mc_key=None):
        super().__init__(xx=1)


@named_as('myitems')
class MyItems(MyItemBase, RepeatableConfigItem):
    def __init__(self, mc_key, xx):
        super().__init__(mc_key=mc_key, xx=xx)


@named_as('myitems')
class MyItemsSingle(MyItems):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, mc_key='predefined')

    def __init__(self, xx):
        super().__init__(mc_key='predefined', xx=xx)


@nested_repeatables('myitems')
class myroot(ConfigItem):
    pass


def test_abstract_config_item_multiple_inheritance_explicit_mc_key():
    @mc_config(ef_pp_prod, load_now=True)
    def config(_):
        with myroot():
            with MyItem() as ci:
                ci.aa = 1
                anitem()

            with MyItems('a', xx=2) as ci:
                ci.aa = 1
                anitem()

            with MyItems('b', xx=3) as ci:
                ci.aa = 2
                anitem()

    cr = config(prod).myroot

    assert cr.myitem.aa == 1
    assert cr.myitems['a'].aa == 1
    assert cr.myitems['b'].aa == 2


def test_abstract_config_item_multiple_inheritance_cls_mc_key():
    @mc_config(ef_pp_prod, load_now=True)
    def config(_):
        with myroot():
            with MyItem() as ci:
                ci.aa = 1
                anitem()

            with MyItems('a', xx=2) as ci:
                ci.aa = 1
                anitem()

            with MyItemsSingle(xx=3) as ci:
                ci.aa = 2
                anitem()

    cr = config(prod).myroot

    assert cr.myitem.aa == 1
    assert cr.myitems['a'].aa == 1
    assert cr.myitems['predefined'].aa == 2
