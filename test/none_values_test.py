# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys

from pytest import raises  # pylint: disable=no-name-in-module

from multiconf import mc_config, ConfigItem, ConfigException
from multiconf.envs import EnvFactory

from .utils.messages import config_error_no_value_expected, config_error_never_received_value_expected
from .utils.utils import next_line_num, start_file_line, lines_in


minor_version = sys.version_info[1]

ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')


def test_attribute_none_args_partial_set_in_init_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, a=None):
            super().__init__()
            # Partial assignment is allowed in init
            self.setattr('a', prod=a)
            self.setattr('b', default=None, prod=2)

        def mc_init(self):
            self.a = 7
            self.b = 7

    @mc_config(ef1_prod_pp, load_now=True)
    def config(_):
        Requires()

    cr = config(prod1)
    assert cr.Requires.a is None  # Note: I pre v6 this would be 7
    assert cr.Requires.b == 2

    cr = config(pp1)
    assert cr.Requires.a == 7 # Value for pp was not set in __init__ so it will get the value from mc_init
    assert cr.Requires.b is None  # Note: I pre v6 this would be 7


def test_attribute_none_args_partial_set_in_init_not_completed(capsys):
    errorline_setattr = [None]
    errorline_exit = [None]

    class Requires(ConfigItem):
        def __init__(self, a=None):
            super().__init__()
            # Partial assignment is allowed in init
            errorline_setattr[0] = next_line_num()
            self.setattr('a', prod=a)
            self.setattr('b', default=None, prod=2)

        def mc_init(self):
            self.b = 7

    with raises(ConfigException):
        errorline_exit[0] = next_line_num() + (1 if minor_version > 7 else 0)
        @mc_config(ef1_prod_pp, load_now=True)
        def config(_):
            Requires()
        # Unresolved partial assignments from __init__

    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline_exit[0]),
        config_error_never_received_value_expected.format(env=pp1),
        start_file_line(__file__, errorline_setattr[0]),
        config_error_no_value_expected.format(attr='a', env=pp1),
    )
