# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class nc_aa_root(ItemWithAA):
    pass


@named_as('children')
class rchild(RepeatableItemWithAA):
    pass


def test_repeatable_items_mc_select_envs_excluded():
    @mc_config(ef)
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

    cr = ef.config(prod).nc_aa_root

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
    with raises(KeyError):
        cr.children['fifth']

    cr = ef.config(pp).nc_aa_root

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
    @mc_config(ef)
    def config(root):
        with nc_aa_root(1) as cr:
            cr.setattr('num_children', pp=2, prod=4, mc_set_unknown=True)
            for ii in range(0, cr.num_children):
                rchild("num" + str(ii), aa=27)

    cr = ef.config(prod).nc_aa_root
    assert len(cr.children) == 4

    cr = ef.config(pp).nc_aa_root
    assert len(cr.children) == 2