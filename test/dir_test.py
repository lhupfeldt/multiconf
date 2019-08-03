# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from multiconf import mc_config, ConfigItem
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
g_p = ef.EnvGroup('g_p', pp, prod)


def test_dir():
    @named_as('someitem')
    @nested_repeatables('RepeatableItems')
    class Nested(ConfigItem):
        @property
        def m(self):
            return 1

    @mc_config(ef, load_now=True)
    def config(rt):
        with ItemWithAA(aa=0) as iaa:
            iaa.setattr('bb', default=1, pp=2, mc_set_unknown=True)
            with Nested() as nn:
                nn.setattr('cc', default=1, prod=2, mc_set_unknown=True)
                with RepeatableItemWithAA('rep1', 7) as rep:
                    rep.setattr('bb', default=1, pp=2, mc_set_unknown=True)

    cr = config(prod)

    iaa = cr.ItemWithAA
    dir_iaa = dir(iaa)
    ojb_dir_iaa = object.__dir__(iaa)
    ojb_dir_iaa = set(sorted(ojb_dir_iaa))
    dir_iaa = set(sorted(dir_iaa))
    assert ojb_dir_iaa >= dir_iaa
    assert 'aa' in dir_iaa
    assert 'bb' in dir_iaa
    assert 'someitem' in dir_iaa

    nested = iaa.someitem
    dir_nested = dir(nested)
    assert set(object.__dir__(nested)) >= set(dir_nested)
    assert 'cc' in dir_nested
    assert 'm' in dir_nested
    assert 'RepeatableItems' in dir_nested

    rep_iaas = nested.RepeatableItems
    for rep_iaa in rep_iaas.values():
        dir_rep_iaa = dir(rep_iaa)
        assert set(object.__dir__(rep_iaa)) >= set(dir_rep_iaa)
        assert 'aa' in dir_rep_iaa
        assert 'bb' in dir_rep_iaa
