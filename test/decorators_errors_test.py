# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from .. import ConfigRoot
from ..decorators import named_as, nested_repeatables, ConfigDefinitionException
from ..envs import EnvFactory

ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')


def test_decorator_arg_is_keyword_in_nested_repeatables_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @nested_repeatables('a, b, def, c')
        class root(ConfigRoot):
            pass

    assert str(exinfo.value) == "'def' is not a valid identifier"


def test_decorator_arg_not_a_valid_identifier_in_named_as_decorator():
    with raises(ConfigDefinitionException) as exinfo:
        @named_as('a-b')
        class root(ConfigRoot):
            pass

    assert str(exinfo.value) == "'a-b' is not a valid identifier"
