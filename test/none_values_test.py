# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import pytest
from pytest import raises  # pylint: disable=no-name-in-module

from .. import ConfigRoot, ConfigItem, ConfigException
from ..envs import EnvFactory

ef1_prod_pp = EnvFactory()
pp1 = ef1_prod_pp.Env('pp')
prod1 = ef1_prod_pp.Env('prod')


def test_attribute_none_args_partial_set_in_init_overridden_in_mc_init():
    class Requires(ConfigItem):
        def __init__(self, a=None):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('a', prod=a)
            self.setattr('b', default=None, prod=2)

        def mc_init(self):
            self.a = 7
            self.b = 7

    with ConfigRoot(prod1, ef1_prod_pp) as cr:
        Requires()

    assert cr.Requires.a == 7
    assert cr.Requires.b == 2

    with ConfigRoot(pp1, ef1_prod_pp) as cr:
        Requires()

    assert cr.Requires.a == 7
    assert cr.Requires.b == 7


def test_attribute_none_args_partial_set_in_init_not_completed():
    class Requires(ConfigItem):
        def __init__(self, a=None):
            super(Requires, self).__init__()
            # Partial assignment is allowed in init
            self.setattr('a', prod=a)
            self.setattr('b', default=None, prod=2)

        def mc_init(self):
            self.b = 7

    with raises(ConfigException):
        with ConfigRoot(prod1, ef1_prod_pp) as cr:
            Requires()
