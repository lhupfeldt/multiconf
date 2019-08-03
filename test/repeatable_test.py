# Copyright (c) 2017 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from pytest import raises

from multiconf import mc_config, ConfigItem
from multiconf.decorators import named_as, nested_repeatables
from multiconf.envs import EnvFactory

from .utils.tstclasses import RepeatableItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class root(ConfigItem):
    pass


def test_manual_insert_in_repeatable_not_allowed():
    with raises(TypeError):
        @mc_config(ef, load_now=True)
        def config(_):
            with root() as cr:
                cr.children['hello'] = 1


def test_get_dict_with_all_items_including_excluded_ones():
    @named_as('children')
    class Child(RepeatableItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with root() as cr:
            Child(mc_key=0, aa=1)
            Child(mc_key=1, aa=2)
            with Child(mc_key=2, aa=3) as ch:
                ch.mc_select_envs(exclude=[pp])

    rt = config(pp).root
    for index, child in rt.children.all_items.items():
        if index != 2:
            assert child
            assert child.aa == index + 1
        else:
            assert not child

    rt = config(prod).root
    for index, child in rt.children.all_items.items():
        assert child
        assert child.aa == index + 1
