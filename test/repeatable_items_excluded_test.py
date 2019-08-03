# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA
from .utils.utils import local_func


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class nc_aa_root(ItemWithAA):
    pass


@named_as('children')
class rchild(RepeatableItemWithAA):
    pass


def test_repeatable_items_mc_select_envs_excluded():
    @mc_config(ef, load_now=True)
    def config(root):
        with nc_aa_root(1) as cr:
            with rchild("first") as ci:
                ci.mc_select_envs(exclude=[prod])
                ci.setattr('aa', pp=1)

            with rchild("second") as ci:
                ci.mc_select_envs(exclude=[pp])
                ci.setattr('aa', prod=2)

            with rchild("third") as ci:
                ci.setattr('aa', prod=3, pp=2)

            with rchild("fourth") as ci:
                ci.setattr('aa', prod=4, pp=3)

            with rchild("fifth") as ci:
                ci.mc_select_envs(exclude=[prod])
                ci.setattr('aa', pp=4)

    cr = config(prod).nc_aa_root

    assert len(cr.children) == 3
    index = 2
    for ci in cr.children.values():
        assert ci.aa == index
        index += 1

    with raises(KeyError):
        cr.children['first']
    assert cr.children['second'].aa == 2
    assert cr.children['third'].aa == 3
    assert cr.children['fourth'].aa == 4
    with raises(KeyError) as exinfo:
        cr.children['fifth']

    assert "'fifth'. 'Excluded: <class 'test.repeatable_items_excluded_test.rchild'>' for Env('prod')." in str(exinfo.value)

    cr = config(pp).nc_aa_root

    assert len(cr.children) == 4
    index = 1
    for ci in cr.children.values():
        assert ci.aa == index
        index += 1

    assert cr.children['first'].aa == 1
    with raises(KeyError):
        cr.children['second']
    assert cr.children['third'].aa == 2
    assert cr.children['fourth'].aa == 3
    assert cr.children['fifth'].aa == 4


def test_repeatable_items_skipped_in_envs():
    @mc_config(ef, load_now=True)
    def config(root):
        with nc_aa_root(1) as cr:
            cr.setattr('num_children', pp=2, prod=4, mc_set_unknown=True)
            for ii in range(0, cr.num_children):
                rchild("num" + str(ii), aa=27)

    cr = config(prod).nc_aa_root
    assert len(cr.children) == 4

    cr = config(pp).nc_aa_root
    assert len(cr.children) == 2


def test_repeatable_items_mc_select_envs_excluded_key_error_property_exception():
    @named_as('children')
    class badchild(RepeatableItemWithAA):
        @property
        def xxx(self):
            raise Exception('bad')

    @mc_config(ef)
    def config(root):
        with nc_aa_root(1) as cr:
            with badchild("first") as ci:
                ci.mc_select_envs(exclude=[prod])
                ci.setattr('aa', pp=1)

    config.load(validate_properties=False)
    cr = config(prod).nc_aa_root

    assert len(cr.children) == 0

    with raises(KeyError) as exinfo:
        cr.children['first']

    ex_msg = str(exinfo.value)
    exp = "'first'. 'Excluded: <class 'test.repeatable_items_excluded_test.%(local_func)sbadchild'>' for Env('prod')." % dict(local_func=local_func())
    assert exp in ex_msg


def test_repeatable_items_mc_select_envs_excluded_key_error_property_attributeerror():
    @named_as('children')
    class badchild(RepeatableItemWithAA):
        @property
        def xxx(self):
            self.no_such_property

    @mc_config(ef)
    def config(root):
        with nc_aa_root(1) as cr:
            with badchild("first") as ci:
                ci.mc_select_envs(exclude=[prod])
                ci.setattr('aa', pp=1)

    config.load(validate_properties=False)
    cr = config(prod).nc_aa_root

    assert len(cr.children) == 0

    with raises(KeyError) as exinfo:
        cr.children['first']

    ex_msg = str(exinfo.value)
    exp = "'first'. 'Excluded: <class 'test.repeatable_items_excluded_test.%(local_func)sbadchild'>' for Env('prod')." % dict(local_func=local_func())
    assert exp in ex_msg


def test_repeatable_items_bool():
    @named_as('Xs')
    class X(RepeatableConfigItem):
        pass

    @named_as('Ys')
    class Y(RepeatableConfigItem):
        pass

    @nested_repeatables('Xs', 'Ys', 'Zs')
    class HasRepeatables(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with HasRepeatables() as y:
            with X(mc_key='aa') as xx:
                xx.mc_select_envs(exclude=[g_prod_like])
            with X(mc_key='bb') as xx:
                xx.mc_select_envs(exclude=[pp])
            with X(mc_key='cc') as xx:
                xx.mc_select_envs(exclude=[g_prod_like])

            Y(mc_key='aa')
            Y(mc_key='bb')
            Y(mc_key='cc')

    rep = config(prod).HasRepeatables
    assert rep.Xs
    assert rep.Ys
    assert not rep.Zs

    rep = config(pp).HasRepeatables
    assert not rep.Xs
    assert rep.Ys
    assert not rep.Zs
