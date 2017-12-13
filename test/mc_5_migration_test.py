# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.messages import config_error_no_value_expected, config_error_never_received_value_expected
from .utils.utils import next_line_num, start_file_line, lines_in


ef_prod_pp = EnvFactory()
pprd = ef_prod_pp.Env('pp')
prod = ef_prod_pp.Env('prod')
g_pap = ef_prod_pp.EnvGroup('g_pap', pprd, prod)


def test_attribute_partial_set_in_init_overridden_in_mc_init_mc_5_migration():
    class Requires(ConfigItem):
        def __init__(self, aa=None):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.aa = aa
            self.setattr('bb', default=None, prod=2)
            self.cc = MC_REQUIRED
            self.setattr('dd', default=None, prod=7)

        def mc_init(self):
            self.aa = 7
            self.bb = 7
            self.cc = 8
            self.setattr('dd', g_pap=8)

    @mc_config(ef_prod_pp, mc_5_migration=True)
    def config(_):
        with Requires() as rq:
            rq.cc = 7

    cr = config(prod)
    assert cr.Requires.aa == 7  # Note: wihout mc_5_migration this whould be None
    assert cr.Requires.bb == 2
    assert cr.Requires.cc == 7
    assert cr.Requires.dd == 7

    cr = config(pprd)
    assert cr.Requires.aa == 7 # Value for pp was not set in __init__ so it will get the value from mc_init 
    assert cr.Requires.bb == 7 # Note: wihout mc_5_migration this whould be None
    assert cr.Requires.cc == 7
    assert cr.Requires.dd == 8
