# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from pytest import fail

from multiconf import mc_config, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAABB


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class nc_aa_root(ConfigItem):
    def __init__(self, aa=None):
        super().__init__()
        self.aa = aa


@named_as('children')
class rchild(RepeatableConfigItem):
    def __new__(cls, name, *args, **kwargs):
        return super().__new__(cls, mc_key=name, *args, **kwargs)

    def __init__(self, name, aa=None, bb=None):
        super().__init__(mc_key=name)
        self.name = name
        self.aa = aa
        self.bb = bb


@named_as('recursive_items')
@nested_repeatables('recursive_items')
class NestedRepeatable(RepeatableConfigItem):
    def __init__(self, mc_key, aa=None):
        super().__init__(mc_key=mc_key)
        self.id = mc_key
        self.aa = aa


def test_nested_repeatable_items():
    @mc_config(ef, load_now=True)
    def config(root):
        with nc_aa_root() as cr:
            with rchild(name="first", aa=1, bb=1) as ci:
                ci.setattr('aa', prod=3)

            with rchild(name="second", aa=4) as ci:
                ci.setattr('bb', prod=2, pp=17)

            with rchild(name="third") as ci:
                ci.setattr('aa', prod=5, pp=18)
                ci.setattr('bb', prod=3, pp=19)

    cr = config(prod).nc_aa_root

    assert cr.children['first'].bb == 1
    assert cr.children['second'].bb == 2
    assert cr.children['third'].bb == 3

    index = 3
    for ci in cr.children.values():
        assert ci.aa == index
        index += 1


def test_empty_nested_repeatable_items():
    @mc_config(ef, load_now=True)
    def config(root):
        nc_aa_root()

    cr = config(prod).nc_aa_root

    for _ci in cr.children.values():
        fail("list should be empty")


def test_automatic_contained_item_freeze_on_exit():
    @nested_repeatables('recursive_items')
    class root2(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(root):
        with root2():
            NestedRepeatable(mc_key='aa')
            with NestedRepeatable(mc_key='bb') as ci:
                NestedRepeatable(mc_key='aa')
                with NestedRepeatable(mc_key='bb') as ci:
                    NestedRepeatable(mc_key='aa')
                    with NestedRepeatable(mc_key='bb') as ci:
                        ci.setattr('aa', prod=1, pp=2)
                    NestedRepeatable(mc_key='cc')
                NestedRepeatable(mc_key='cc')
            NestedRepeatable(mc_key='cc')

    cr = config(prod).root2
    assert len(cr.recursive_items['aa'].recursive_items) == 0
    assert len(cr.recursive_items['bb'].recursive_items) == 3
    assert len(cr.recursive_items['cc'].recursive_items) == 0

    ids = ['aa', 'bb', 'cc']
    index = 0
    for item_id, item in cr.recursive_items['bb'].recursive_items.items():
        assert item.id == ids[index]
        assert item_id == ids[index]
        index += 1
    assert index == 3

    assert cr.recursive_items['bb'].recursive_items['bb'].recursive_items['bb'].aa == 1


def test_mc_init_repeatable_items():
    class X(RepeatableConfigItem):
        def __init__(self, mc_key, aa, bb=None):
            super().__init__(mc_key)
            self.aa = aa
            if bb is not None:
                self.bb = bb

    @nested_repeatables('Xs')
    class Y(ItemWithAABB):
        def mc_init(self):
            self.aa = 1
            self.bb = 1
            with X(mc_key='aa', aa=1, bb=1) as x:
                x.setattr('aa', prod=7)
            X(mc_key='bb', aa=1, bb=2)
            X(mc_key='cc', aa=1, bb=1)

    @mc_config(ef, load_now=True)
    def config(_):
        with Y() as y:
            y.aa = 3
            with X(mc_key='aa', aa=1) as x:
                x.aa = 3
            with X(mc_key='bb', aa=1) as x:
                x.aa = 3

    cr = config(prod)

    assert cr.Y.aa == 3
    assert cr.Y.Xs['aa'].aa == 7  # v6 change, pre v6 this was 3, now it will be 7  because of object merge
    assert cr.Y.Xs['aa'].bb == 1
    assert cr.Y.Xs['bb'].aa == 3
    assert cr.Y.Xs['bb'].bb == 2
    assert cr.Y.Xs['cc'].aa == 1
    assert cr.Y.Xs['cc'].bb == 1


def test_repeatable_items_get():
    class X(RepeatableConfigItem):
        pass

    @nested_repeatables('Xs')
    class Y(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with Y() as y:
            X(mc_key='aa')
            X(mc_key='bb')

    cr = config(prod)

    assert cr.Y.Xs.get('aa')
    assert cr.Y.Xs.get('cc') is None


def test_repeatable_items_equal():
    @named_as('Xs')
    class X(RepeatableConfigItem):
        pass

    @named_as('Ys')
    class Y(RepeatableConfigItem):
        pass

    @named_as('Zs')
    class Z(RepeatableConfigItem):
        pass

    @nested_repeatables('Xs', 'Ys', 'Zs')
    class HasRepeatables(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with HasRepeatables() as y:
            X(mc_key='aa')
            X(mc_key='bb')
            Y(mc_key='aa')
            Z(mc_key='aa')
            Z(mc_key='bb')

    cr = config(prod)

    assert cr.HasRepeatables.Xs == cr.HasRepeatables.Xs
    # assert cr.HasRepeatables.Xs == cr.HasRepeatables.Zs  # TODO? Equality between different dicts?
    assert cr.HasRepeatables.Xs != cr.HasRepeatables.Ys
    assert cr.HasRepeatables.Ys != cr.HasRepeatables.Zs


def test_repeatable_items_iter():
    @named_as('Xs')
    class X(RepeatableConfigItem):
        pass

    @nested_repeatables('Xs', 'Ys', 'Zs')
    class HasRepeatables(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with HasRepeatables() as y:
            X(mc_key='aa')
            X(mc_key='bb')
            X(mc_key='cc')

    cr = config(prod)

    keys = []
    for key in cr.HasRepeatables.Xs:
        keys.append(key)
    assert keys == ['aa', 'bb', 'cc']
